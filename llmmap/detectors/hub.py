"""Detector hub: consensus scoring, calibration, and dedupe signatures."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from llmmap.detectors.base import DetectorResult
from llmmap.detectors.judge import LLMJudgeConfig, LLMJudgeDetector
from llmmap.detectors.semantic import SemanticEmbeddingDetector

_OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "https://api.ollama.com")


class DetectorHub:
    """Runs detector layers and returns consensus score."""

    def __init__(
        self,
        threshold: float = 0.6,
        fp_suppression: bool = True,
        *,
        semantic_use_provider: bool = False,
        semantic_provider_url: str = f"{_OLLAMA_BASE}/api/embeddings",
        semantic_provider_model: str = "nomic-embed-text",
        semantic_provider_timeout: float = 20.0,
        llm_judge_enabled: bool = False,
        llm_judge_model: str = os.environ.get("OLLAMA_MODEL", "qwen3-coder-next:cloud"),
        llm_judge_url: str = f"{_OLLAMA_BASE}/api/chat",
        llm_judge_timeout: float = 60.0,
        llm_client: Any | None = None,
    ) -> None:
        self._threshold = threshold
        self._fp_suppression = fp_suppression
        self._semantic = SemanticEmbeddingDetector(
            provider=SemanticEmbeddingDetector.ProviderConfig(
                enabled=semantic_use_provider,
                url=semantic_provider_url,
                model=semantic_provider_model,
                timeout_seconds=semantic_provider_timeout,
            )
        )
        self._llm_judge = LLMJudgeDetector(
            LLMJudgeConfig(
                enabled=llm_judge_enabled,
                model=llm_judge_model,
                url=llm_judge_url,
                timeout_seconds=llm_judge_timeout,
                llm_client=llm_client,
            )
        )

    def evaluate(
        self,
        prompt_text: str,
        response_text: str,
        status_code: int,
        *,
        skip_llm: bool = False,
    ) -> DetectorResult:
        """Run detectors and return consensus score.

        When skip_llm=True, only run the cheap semantic detector (no Ollama call).
        This is used in two-phase detection where the combined judge handles
        the LLM evaluation separately.
        """
        semantic = self._semantic.evaluate(prompt_text, response_text, status_code)

        if skip_llm:
            score = semantic.score
            hits = list(semantic.hits)
            raw = {
                "semantic_score": f"{semantic.score:.3f}",
                "llm_judge_score": "skipped",
                "threshold": f"{self._threshold:.3f}",
                "signal_count": str(len(semantic.hits)),
            }
        else:
            llm_judge = self._llm_judge.evaluate(prompt_text, response_text, status_code)
            score = min(
                1.0,
                (llm_judge.score * 0.85) + (semantic.score * 0.15),
            )
            hits = [*semantic.hits, *llm_judge.hits]
            raw = {
                "semantic_score": f"{semantic.score:.3f}",
                "llm_judge_score": f"{llm_judge.score:.3f}",
                "threshold": f"{self._threshold:.3f}",
                "signal_count": str(len(hits)),
            }

        suppressed = False
        suppress_reason = ""
        if self._fp_suppression:
            if status_code >= 500:
                suppressed = True
                suppress_reason = "server_error_response"
            elif not response_text or response_text.strip() == "":
                suppressed = True
                suppress_reason = "empty_response"

        label = "none"
        if score >= 0.8:
            label = "high"
        elif score >= 0.6:
            label = "medium"
        elif score >= 0.4:
            label = "low"

        return DetectorResult(
            score=score,
            label=label,
            suppressed=suppressed,
            suppress_reason=suppress_reason,
            hits=hits,
            raw=raw,
        )

    def is_positive(self, result: DetectorResult) -> bool:
        return result.score >= self._threshold and not result.suppressed



def finding_signature(prompt_id: str, point_id: str, hit_rule_ids: list[str]) -> str:
    prompt = {
        "prompt_id": prompt_id,
        "point_id": point_id,
        "hit_rule_ids": sorted(hit_rule_ids),
    }
    packed = json.dumps(prompt, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()
