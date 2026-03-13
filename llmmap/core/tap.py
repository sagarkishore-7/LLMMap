"""TAP (Tree of Attacks with Pruning) engine for Stage 3."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class TapConfig:
    depth: int
    width: int
    branching_factor: int
    min_score: float
    drift_patience: int
    drift_similarity_threshold: float
    query_budget: int


@dataclass
class TapNode:
    node_id: str
    parent_id: str | None
    depth: int
    prompt: str
    phase1_score: float = 0.0
    target_score: float = 0.0
    total_score: float = 0.0
    success: bool = False
    status: str = "candidate"
    pruned_reason: str = ""
    response_excerpt: str = ""
    cost_usd: float = 0.0
    token_estimate: int = 0


@dataclass
class TapIteration:
    depth: int
    candidates: int
    after_phase1: int
    queried: int
    kept: int
    best_score: float


@dataclass
class TapTrace:
    goal: str
    target_str: str
    config: TapConfig
    nodes: list[TapNode] = field(default_factory=list)
    iterations: list[TapIteration] = field(default_factory=list)
    success_node_id: str | None = None
    stop_reason: str = "completed"
    total_queries: int = 0


@dataclass(frozen=True)
class TapAssessResult:
    score: float
    success: bool
    response_excerpt: str
    cost_usd: float
    token_estimate: int


def run_tap(
    *,
    seed_prompts: list[str],
    goal: str,
    target_str: str,
    config: TapConfig,
    attacker_expand: Callable[[str, int, int], list[str]],
    phase1_eval: Callable[[str, str], float],
    assess_target: Callable[[str, int], TapAssessResult],
) -> TapTrace:
    """Run TAP loop with semantic drift pruning and budget-aware expansion."""
    trace = TapTrace(goal=goal, target_str=target_str, config=config)
    frontier = [
        TapNode(node_id=f"tap-{uuid4().hex[:8]}", parent_id=None, depth=0, prompt=prompt)
        for prompt in _dedupe(seed_prompts)
    ][: max(1, config.width)]
    trace.nodes.extend(frontier)

    best_so_far = 0.0
    stagnant_steps = 0
    queries_used = 0

    for depth in range(max(1, config.depth)):
        if queries_used >= config.query_budget:
            trace.stop_reason = "query_budget_exhausted"
            break
        if not frontier:
            trace.stop_reason = "empty_frontier"
            break

        candidates: list[TapNode] = []
        for parent in frontier:
            expansions = attacker_expand(parent.prompt, config.branching_factor, depth)
            for prompt in _dedupe(expansions)[: max(1, config.branching_factor)]:
                node = TapNode(
                    node_id=f"tap-{uuid4().hex[:8]}",
                    parent_id=parent.node_id,
                    depth=depth + 1,
                    prompt=prompt,
                )
                node.phase1_score = float(phase1_eval(goal, prompt))
                candidates.append(node)

        if not candidates:
            trace.stop_reason = "no_candidates"
            break

        drift_kept: list[TapNode] = []
        for node in candidates:
            similarity = _semantic_similarity(goal, node.prompt)
            if similarity < config.drift_similarity_threshold:
                node.status = "pruned_drift"
                node.pruned_reason = (
                    f"goal_similarity={similarity:.3f}<threshold={config.drift_similarity_threshold:.3f}"
                )
                continue
            drift_kept.append(node)
        if not drift_kept:
            trace.nodes.extend(candidates)
            trace.stop_reason = "drift_detected"
            break

        candidates = drift_kept
        candidates.sort(key=lambda item: item.phase1_score, reverse=True)
        phase1_cutoff = max(config.width, config.width * config.branching_factor // 2)
        phase1_kept = candidates[:phase1_cutoff]
        for node in candidates[phase1_cutoff:]:
            node.status = "pruned_phase1"
            node.pruned_reason = "off_topic_or_low_relevance"

        queried_nodes: list[TapNode] = []
        for node in phase1_kept:
            if queries_used >= config.query_budget:
                node.status = "skipped_budget"
                continue
            assessment: TapAssessResult = assess_target(node.prompt, depth)
            node.target_score = assessment.score
            node.total_score = min(1.0, (0.35 * node.phase1_score) + (0.65 * node.target_score))
            node.success = assessment.success or node.total_score >= config.min_score
            node.response_excerpt = assessment.response_excerpt
            node.cost_usd = assessment.cost_usd
            node.token_estimate = assessment.token_estimate
            node.status = "queried"
            queries_used += 1
            queried_nodes.append(node)
            if node.success:
                trace.success_node_id = node.node_id
                trace.stop_reason = "success"
                break

        trace.nodes.extend(candidates)
        if trace.success_node_id is not None:
            best = max((node.total_score for node in queried_nodes), default=0.0)
            trace.iterations.append(
                TapIteration(
                    depth=depth,
                    candidates=len(candidates),
                    after_phase1=len(phase1_kept),
                    queried=len(queried_nodes),
                    kept=1,
                    best_score=best,
                )
            )
            break

        queried_nodes.sort(key=lambda item: item.total_score, reverse=True)
        frontier = queried_nodes[: max(1, config.width)]
        for node in queried_nodes[max(1, config.width) :]:
            node.status = "pruned_phase2"
            node.pruned_reason = "low_combined_score"

        best = max((node.total_score for node in queried_nodes), default=0.0)
        trace.iterations.append(
            TapIteration(
                depth=depth,
                candidates=len(candidates),
                after_phase1=len(phase1_kept),
                queried=len(queried_nodes),
                kept=len(frontier),
                best_score=best,
            )
        )

        if best <= best_so_far + 0.02:
            stagnant_steps += 1
            if stagnant_steps >= max(1, config.drift_patience):
                trace.stop_reason = "drift_detected"
                break
        else:
            stagnant_steps = 0
            best_so_far = best

    trace.total_queries = queries_used
    if trace.success_node_id is None and trace.stop_reason == "completed":
        trace.stop_reason = "depth_exhausted"
    return trace


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _semantic_similarity(goal: str, prompt: str) -> float:
    goal_terms = set(re.findall(r"[A-Za-z0-9_]{4,}", goal.lower()))
    prompt_terms = set(re.findall(r"[A-Za-z0-9_]{4,}", prompt.lower()))
    if not goal_terms or not prompt_terms:
        return 0.0
    inter = len(goal_terms.intersection(prompt_terms))
    union = len(goal_terms.union(prompt_terms))
    if union == 0:
        return 0.0
    return inter / union
