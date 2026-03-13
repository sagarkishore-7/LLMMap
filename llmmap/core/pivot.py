"""Pivot/context feedback extraction and canonicalization helpers."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from llmmap.core.models import EvidenceRecord, Finding


@dataclass
class PivotArtifacts:
    system_context: list[str] = field(default_factory=list)
    rag_sources: list[str] = field(default_factory=list)
    tool_list: list[str] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)

    def context_vars(self) -> dict[str, str]:
        return {
            "SYSTEM_CONTEXT": " | ".join(self.system_context[:5]),
            "RAG_SOURCES": ",".join(self.rag_sources[:8]),
            "FOUND_TOOLS": ",".join(self.tool_list[:8]),
            "FOUND_ENDPOINTS": ",".join(self.endpoints[:8]),
        }


@dataclass(frozen=True)
class PivotEvent:
    evidence_id: str
    finding_id: str
    extracted: dict[str, list[str]]


def extract_pivot_artifacts(
    evidence: list[EvidenceRecord],
    findings: list[Finding],
) -> tuple[PivotArtifacts, list[PivotEvent]]:
    by_evidence = {record.evidence_id: record for record in evidence}
    artifacts = PivotArtifacts()
    events: list[PivotEvent] = []

    for finding in findings:
        extracted: dict[str, list[str]] = {
            "system_context": [],
            "rag_sources": [],
            "tool_list": [],
            "endpoints": [],
        }
        for evidence_id in finding.evidence_ids:
            record = by_evidence.get(evidence_id)
            if record is None:
                continue
            source = _flatten_record(record)
            extracted["system_context"].extend(_extract_system_context(source))
            extracted["rag_sources"].extend(_extract_rag_sources(source))
            extracted["tool_list"].extend(_extract_tool_names(source))
            extracted["endpoints"].extend(_extract_endpoints(source))

        _merge_unique(artifacts.system_context, extracted["system_context"])
        _merge_unique(artifacts.rag_sources, extracted["rag_sources"])
        _merge_unique(artifacts.tool_list, extracted["tool_list"])
        _merge_unique(artifacts.endpoints, extracted["endpoints"])
        events.append(
            PivotEvent(
                evidence_id=",".join(finding.evidence_ids),
                finding_id=finding.finding_id,
                extracted=extracted,
            )
        )

    return artifacts, events


def write_pivot_trace(path: Path, artifacts: PivotArtifacts, events: list[PivotEvent]) -> None:
    data = {
        "canonicalized": asdict(artifacts),
        "events": [asdict(item) for item in events],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _flatten_record(record: EvidenceRecord) -> str:
    chunks = [
        json.dumps(record.request_snapshot, sort_keys=True),
        json.dumps(record.response_snapshot, sort_keys=True),
        json.dumps(record.detector_outputs, sort_keys=True),
    ]
    return "\n".join(chunks)


def _extract_system_context(text: str) -> list[str]:
    out = []
    patterns = [
        r"(system prompt[^\"\\n]{0,180})",
        r"(developer instructions[^\"\\n]{0,180})",
        r"(internal policy[^\"\\n]{0,180})",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            out.append(match.strip())
    return out


def _extract_rag_sources(text: str) -> list[str]:
    out = []
    for match in re.findall(
        r"([\w./-]+\.(?:md|txt|pdf|docx|json))",
        text,
        flags=re.IGNORECASE,
    ):
        out.append(match.strip())
    return out


def _extract_tool_names(text: str) -> list[str]:
    out = []
    for match in re.findall(
        r"\b(tool|function|plugin|connector)[_: -]?([A-Za-z0-9_\-]{2,40})",
        text,
        flags=re.IGNORECASE,
    ):
        out.append(f"{match[0]}:{match[1]}")
    return out


def _extract_endpoints(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.findall(
            r"(https?://[^\"'\\s]+)",
            text,
            flags=re.IGNORECASE,
        )
    ]


def _merge_unique(dst: list[str], src: list[str]) -> None:
    seen = {item.lower() for item in dst}
    for item in src:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        dst.append(normalized)
