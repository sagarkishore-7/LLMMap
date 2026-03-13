from __future__ import annotations

from llmmap.core.models import EvidenceRecord, Finding
from llmmap.core.pivot import extract_pivot_artifacts


def test_extract_pivot_artifacts_collects_context_tools_and_endpoints() -> None:
    evidence = [
        EvidenceRecord(
            evidence_id="ev-1",
            stage="stage1",
            request_snapshot={"url": "https://api.example.com/chat"},
            response_snapshot={
                "body": "system prompt says use tool_fetch and source policy_notes.md",
                "status_code": "200",
            },
            detector_outputs={"note": "internal policy leaked"},
            confidence=0.9,
        )
    ]
    findings = [
        Finding(
            finding_id="fi-1",
            finding_type="direct",
            title="Leak",
            severity="high",
            confidence=0.9,
            reproducibility="x",
            evidence_ids=["ev-1"],
            notes="",
        )
    ]

    artifacts, events = extract_pivot_artifacts(evidence, findings)
    assert events
    assert artifacts.system_context
    assert artifacts.rag_sources
    assert artifacts.tool_list
    assert artifacts.endpoints
