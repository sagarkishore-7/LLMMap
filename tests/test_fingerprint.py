"""Tests for the Stage 0 fingerprinting data model and plumbing."""

from __future__ import annotations

import json

from llmmap.core.fingerprint import (
    FingerprintResult,
    GuardrailProfile,
    ModelFamilyEstimate,
)


def test_default_fingerprint_result() -> None:
    fp = FingerprintResult()
    assert fp.status == "skipped"
    assert fp.top_family == "unknown"
    assert fp.top_family_confidence == 0.0
    assert fp.probe_count == 0


def test_fingerprint_result_to_dict_roundtrip() -> None:
    fp = FingerprintResult(
        status="ok",
        probe_count=18,
        elapsed_ms=5400.0,
        top_family="gpt-4",
        top_family_confidence=0.72,
        family_estimates=(
            ModelFamilyEstimate(family="gpt-4", probability=0.72, signals=("identity_match",)),
            ModelFamilyEstimate(family="unknown", probability=0.28, signals=()),
        ),
        guardrails=GuardrailProfile(
            refuses_harmful_content=True,
            refuses_system_prompt_disclosure=True,
            refusal_style="polite",
        ),
    )
    d = fp.to_dict()

    # Verify structure
    assert d["status"] == "ok"
    assert d["top_family"] == "gpt-4"
    assert d["top_family_confidence"] == 0.72
    assert len(d["family_estimates"]) == 2
    assert d["family_estimates"][0]["family"] == "gpt-4"
    assert d["family_estimates"][0]["signals"] == ["identity_match"]
    assert d["guardrails"]["refuses_harmful_content"] is True
    assert d["guardrails"]["refusal_style"] == "polite"

    # Verify JSON serializable
    serialized = json.dumps(d)
    assert json.loads(serialized) == d


def test_default_guardrail_profile() -> None:
    gp = GuardrailProfile()
    assert gp.refuses_harmful_content is False
    assert gp.refusal_style == "unknown"
    assert gp.content_filter_detected is False


def test_model_family_estimate_defaults() -> None:
    e = ModelFamilyEstimate(family="claude-3", probability=0.5)
    assert e.signals == ()
