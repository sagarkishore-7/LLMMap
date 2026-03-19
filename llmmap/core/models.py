"""Core typed models for Week 2 scan flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str]
    body: str


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    body: str
    elapsed_ms: float
    error: str | None = None
    from_cache: bool = False


@dataclass(frozen=True)
class InjectionPoint:
    point_id: str
    location: str
    key: str
    original_value: str


@dataclass(frozen=True)
class StageResult:
    stage: str
    status: str
    details: dict[str, str]


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    stage: str
    request_snapshot: dict[str, str]
    response_snapshot: dict[str, str]
    detector_outputs: dict[str, str]
    confidence: float


@dataclass(frozen=True)
class Finding:
    finding_id: str
    finding_type: str
    title: str
    severity: str
    confidence: float
    reproducibility: str
    evidence_ids: list[str]
    notes: str = ""
    prompt_text: str = ""
    rule_id: str = ""
    point_id: str = ""


@dataclass
class ScanReport:
    status: str
    mode: str
    target_url: str
    run_dir: str
    stage_results: list[StageResult] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    fingerprint: dict[str, Any] | None = None
