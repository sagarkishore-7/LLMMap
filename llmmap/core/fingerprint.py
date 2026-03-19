"""Model fingerprinting data model and Stage 0 stub.

This module defines the data structures for Stage 0 fingerprinting
results.  Actual probe logic and classification will be added in a
later phase — see docs/FINGERPRINTING_DESIGN.md for the full spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelFamilyEstimate:
    """Probability estimate for a single model family."""

    family: str  # e.g. "gpt-4", "claude-3", "llama-3", "unknown"
    probability: float  # [0.0, 1.0]
    signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class GuardrailProfile:
    """Observed guardrail behaviors (populated by future probe analysis)."""

    refuses_harmful_content: bool = False
    refuses_personal_data: bool = False
    refuses_system_prompt_disclosure: bool = False
    refuses_role_override: bool = False
    refusal_style: str = "unknown"  # "polite", "terse", "silent", "error_code", "unknown"
    content_filter_detected: bool = False


@dataclass
class FingerprintResult:
    """Complete output of Stage 0 fingerprinting.

    When fingerprinting is disabled or skipped (dry mode), `status` is
    ``"skipped"`` and all fields retain their defaults.
    """

    stage: str = "stage0_fingerprint"
    status: str = "skipped"  # "ok", "partial", "skipped"
    probe_count: int = 0
    elapsed_ms: float = 0.0

    family_estimates: tuple[ModelFamilyEstimate, ...] = ()
    top_family: str = "unknown"
    top_family_confidence: float = 0.0

    guardrails: GuardrailProfile = field(default_factory=GuardrailProfile)

    response_language: str = "en"
    avg_response_length: int = 0
    follows_formatting_instructions: bool = True
    echoes_input_tokens: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        return {
            "stage": self.stage,
            "status": self.status,
            "probe_count": self.probe_count,
            "elapsed_ms": self.elapsed_ms,
            "top_family": self.top_family,
            "top_family_confidence": self.top_family_confidence,
            "family_estimates": [
                {
                    "family": e.family,
                    "probability": e.probability,
                    "signals": list(e.signals),
                }
                for e in self.family_estimates
            ],
            "guardrails": {
                "refuses_harmful_content": self.guardrails.refuses_harmful_content,
                "refuses_personal_data": self.guardrails.refuses_personal_data,
                "refuses_system_prompt_disclosure": self.guardrails.refuses_system_prompt_disclosure,
                "refuses_role_override": self.guardrails.refuses_role_override,
                "refusal_style": self.guardrails.refusal_style,
                "content_filter_detected": self.guardrails.content_filter_detected,
            },
            "response_language": self.response_language,
            "avg_response_length": self.avg_response_length,
            "follows_formatting_instructions": self.follows_formatting_instructions,
            "echoes_input_tokens": self.echoes_input_tokens,
        }
