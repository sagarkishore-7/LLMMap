"""Detector models and interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class DetectorHit:
    detector: str
    rule_id: str
    reason: str
    weight: float
    snippet: str = ""


@dataclass
class DetectorResult:
    score: float
    label: str
    suppressed: bool
    suppress_reason: str = ""
    hits: list[DetectorHit] = field(default_factory=list)
    raw: dict[str, str] = field(default_factory=dict)


class Detector(Protocol):
    """Detector interface contract."""

    def evaluate(self, prompt_text: str, response_text: str, status_code: int) -> DetectorResult:
        """Evaluate request/response pair and return score + hits."""

