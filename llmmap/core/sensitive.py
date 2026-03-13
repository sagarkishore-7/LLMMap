"""Sensitive artifact retention helpers."""

from __future__ import annotations

from pathlib import Path

_SENSITIVE_ARTIFACTS = (
    "artifacts/pivot_trace.json",
    "artifacts/oob_events.json",
    "artifacts/tap_trace.json",
    "artifacts/tap_events.json",
)


def purge_sensitive_artifacts(run_dir: Path) -> list[str]:
    removed: list[str] = []
    for rel in _SENSITIVE_ARTIFACTS:
        candidate = run_dir / rel
        if not candidate.exists():
            continue
        candidate.unlink()
        removed.append(rel)
    return removed
