"""Audit helpers for run lifecycle events."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def append_audit_event(
    audit_file: Path,
    *,
    operator_id: str,
    event: str,
    run_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "operator_id": operator_id,
        "event": event,
        "run_id": run_id,
        "details": details or {},
    }
    with audit_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
