"""Shared data models for PromptLab engine and API."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Mode(str, Enum):
    VULNERABLE = "vulnerable"
    DEFENDED = "defended"


@dataclass(frozen=True)
class ChatMessage:
    """Single message in the simulation transcript.

    Attributes:
        role: One of ``"system"``, ``"user"``, or ``"assistant"``.
        content: The message text.
        is_injection: ``True`` when this message carries an attack payload.
    """

    role: str
    content: str
    is_injection: bool = False


@dataclass(frozen=True)
class TechniqueInfo:
    """Human-readable technique metadata for the explanation panel."""

    technique_id: str
    family: str
    name: str
    description: str
    owasp_tag: str
    why_it_works: str
    how_to_mitigate: str


@dataclass(frozen=True)
class JudgeVerdict:
    """Outcome produced by the judge after analysing the target response.

    Attributes:
        attack_succeeded: Whether the attacker's goal was achieved.
        confidence: Score in [0, 1] indicating judge certainty.
        reasoning: Human-readable explanation of the verdict.
        method: How the verdict was reached — ``"deterministic"`` (known
            secret matched), ``"heuristic"`` (pattern-based), ``"llm"``
            (model-based, future), or ``"none"`` (default placeholder).
    """

    attack_succeeded: bool
    confidence: float
    reasoning: str
    method: str


@dataclass
class SimulationResult:
    """Full result of a single simulation run."""

    scenario_id: str
    technique_id: str
    mode: str  # "vulnerable" or "defended"
    messages: list[ChatMessage] = field(default_factory=list)
    verdict: JudgeVerdict = field(
        default_factory=lambda: JudgeVerdict(
            attack_succeeded=False, confidence=0.0, reasoning="", method="none",
        )
    )
    technique_info: TechniqueInfo | None = None
    target_system_prompt: str = ""  # Revealed after simulation for educational value
    defense_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "technique_id": self.technique_id,
            "mode": self.mode,
            "messages": [
                {"role": m.role, "content": m.content, "is_injection": m.is_injection}
                for m in self.messages
            ],
            "verdict": {
                "attack_succeeded": self.verdict.attack_succeeded,
                "confidence": self.verdict.confidence,
                "reasoning": self.verdict.reasoning,
                "method": self.verdict.method,
            },
            "technique_info": {
                "technique_id": self.technique_info.technique_id,
                "family": self.technique_info.family,
                "name": self.technique_info.name,
                "description": self.technique_info.description,
                "owasp_tag": self.technique_info.owasp_tag,
                "why_it_works": self.technique_info.why_it_works,
                "how_to_mitigate": self.technique_info.how_to_mitigate,
            }
            if self.technique_info
            else None,
            "target_system_prompt": self.target_system_prompt,
            "defense_description": self.defense_description,
        }
