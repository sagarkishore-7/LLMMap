from __future__ import annotations

from llmmap.core.tap import TapAssessResult, TapConfig, run_tap


def test_tap_finds_successful_branch() -> None:
    config = TapConfig(
        depth=3,
        width=2,
        branching_factor=2,
        min_score=0.6,
        drift_patience=2,
        drift_similarity_threshold=0.0,
        query_budget=10,
    )

    def attacker_expand(prompt: str, branching: int, depth: int) -> list[str]:
        return [f"{prompt} variant_{depth}_{idx}" for idx in range(branching)]

    def phase1_eval(goal: str, prompt: str) -> float:
        return 1.0 if "variant_1_1" in prompt else 0.6

    def assess(prompt: str, depth: int) -> TapAssessResult:
        success = "variant_1_1" in prompt
        return TapAssessResult(
            score=0.9 if success else 0.3,
            success=success,
            response_excerpt="ok",
            cost_usd=0.001,
            token_estimate=100,
        )

    trace = run_tap(
        seed_prompts=["seed"],
        goal="reveal hidden prompt",
        target_str="system prompt",
        config=config,
        attacker_expand=attacker_expand,
        phase1_eval=phase1_eval,
        assess_target=assess,
    )

    assert trace.success_node_id is not None
    assert trace.stop_reason == "success"
    assert trace.total_queries >= 1


def test_tap_stops_on_drift() -> None:
    config = TapConfig(
        depth=4,
        width=2,
        branching_factor=2,
        min_score=0.8,
        drift_patience=1,
        drift_similarity_threshold=0.05,
        query_budget=20,
    )

    def attacker_expand(prompt: str, branching: int, depth: int) -> list[str]:
        return [f"{prompt}-x{idx}" for idx in range(branching)]

    def phase1_eval(goal: str, prompt: str) -> float:
        return 0.5

    def assess(prompt: str, depth: int) -> TapAssessResult:
        return TapAssessResult(
            score=0.2,
            success=False,
            response_excerpt="no-signal",
            cost_usd=0.001,
            token_estimate=50,
        )

    trace = run_tap(
        seed_prompts=["seed"],
        goal="goal",
        target_str="target",
        config=config,
        attacker_expand=attacker_expand,
        phase1_eval=phase1_eval,
        assess_target=assess,
    )

    assert trace.success_node_id is None
    assert trace.stop_reason in {"drift_detected", "depth_exhausted"}


def test_tap_semantic_drift_prunes_off_topic_candidates() -> None:
    config = TapConfig(
        depth=3,
        width=2,
        branching_factor=2,
        min_score=0.9,
        drift_patience=2,
        drift_similarity_threshold=0.5,
        query_budget=10,
    )

    def attacker_expand(prompt: str, branching: int, depth: int) -> list[str]:
        return [f"weather forecast city {idx}" for idx in range(branching)]

    def phase1_eval(goal: str, prompt: str) -> float:
        return 0.9

    def assess(prompt: str, depth: int) -> TapAssessResult:
        return TapAssessResult(
            score=0.0,
            success=False,
            response_excerpt="none",
            cost_usd=0.0,
            token_estimate=0,
        )

    trace = run_tap(
        seed_prompts=["seed"],
        goal="reveal hidden system instructions and policy",
        target_str="system prompt",
        config=config,
        attacker_expand=attacker_expand,
        phase1_eval=phase1_eval,
        assess_target=assess,
    )

    assert trace.success_node_id is None
    assert trace.stop_reason == "drift_detected"
    assert any(node.status == "pruned_drift" for node in trace.nodes)
