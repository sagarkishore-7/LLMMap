"""Baseline reporting utilities."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from llmmap.core.models import ScanReport


def write_json_report(path: Path, prompt: dict[str, Any]) -> None:
    path.write_text(json.dumps(prompt, indent=2), encoding="utf-8")


def write_scan_report(path: Path, report: ScanReport) -> None:
    """Serialize typed scan report into JSON."""
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")


def write_markdown_report(path: Path, report: ScanReport) -> None:
    """Write a concise markdown report for human review."""
    lines = [
        "# LLMMap Scan Report",
        "",
        f"- Status: `{report.status}`",
        f"- Mode: `{report.mode}`",
        f"- Target: `{report.target_url}`",
        f"- Evidence records: `{len(report.evidence)}`",
        f"- Findings: `{len(report.findings)}`",
        "",
        "## Stages",
        "",
        "| Stage | Status | Details |",
        "|---|---|---|",
    ]
    for stage in report.stage_results:
        detail = ", ".join(f"{key}={value}" for key, value in stage.details.items())
        lines.append(f"| `{stage.stage}` | `{stage.status}` | {detail} |")

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| ID | Type | Severity | Confidence | Title | Reproducibility |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for finding in report.findings:
        lines.append(
            "| "
            f"`{finding.finding_id}` | `{finding.finding_type}` | `{finding.severity}` | "
            f"{finding.confidence:.2f} | {finding.title} | `{finding.reproducibility}` |"
        )
    if not report.findings:
        lines.append("| - | - | - | - | No findings | - |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
