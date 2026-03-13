from __future__ import annotations

from llmmap.core.pattern_detection import (
    evaluate_prompt_patterns,
    evaluate_user_patterns,
    merge_detector_results,
)
from llmmap.detectors.base import DetectorResult
from llmmap.prompts.schema import PromptTechnique


def test_evaluate_prompt_patterns_matches_success_and_suppress_rules() -> None:
    prompt = PromptTechnique(
        prompt_id="demo",
        family="instruction_manipulation",
        technique="demo",
        template="probe",
        requires=("chat",),
        tags=("llm01",),
        stage="stage1",
        success_patterns=(r"system prompt", r"api[_ -]?key"),
        suppress_patterns=(r"cannot help with that",),
    )

    response = "I can share system prompt and API_KEY references."
    result = evaluate_prompt_patterns(prompt, response)
    assert result.score >= 0.5
    assert len(result.hits) >= 2
    assert result.suppressed is False

    suppressed = evaluate_prompt_patterns(prompt, "I cannot help with that.")
    assert suppressed.suppressed is True


def test_merge_detector_results_blends_scores_and_hits() -> None:
    base = DetectorResult(
        score=0.6,
        label="medium",
        suppressed=False,
        hits=[],
        raw={"heuristic_score": "0.600"},
    )
    pattern = DetectorResult(
        score=1.0,
        label="high",
        suppressed=False,
        hits=[],
        raw={"pattern_count": "2"},
    )

    merged = merge_detector_results(base, pattern)
    assert merged.score > base.score
    assert merged.raw["prompt_pattern_score"] == "1.000"


def test_evaluate_user_patterns_matches_regex_and_keywords() -> None:
    response = "Leaked material: api_key=abc123 and secret_key=xyz"
    result = evaluate_user_patterns(
        response_text=response,
        regex_patterns=(r"api[_ -]?key\s*=\s*[A-Za-z0-9]+",),
        keywords=("secret_key",),
    )
    assert result.score >= 0.8
    assert len(result.hits) >= 2
