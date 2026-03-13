"""Run directory and artifact management."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from llmmap.config import RuntimeConfig
from llmmap.core.audit import append_audit_event


def _build_run_id(now: datetime) -> str:
    return f"{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"



def create_run_workspace(config: RuntimeConfig) -> Path:
    """Create run workspace and baseline artifact folders."""
    now = datetime.now(UTC)
    if config.purge_old_runs and config.retention_days > 0:
        _purge_old_run_dirs(config.run_root, config.retention_days)
    run_id = _build_run_id(now)

    run_dir = config.run_root / run_id
    logs_dir = run_dir / "logs"
    artifacts_dir = run_dir / "artifacts"
    findings_dir = run_dir / "findings"

    for directory in (run_dir, logs_dir, artifacts_dir, findings_dir):
        directory.mkdir(parents=True, exist_ok=False)

    def _json_safe(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, tuple):
            return list(value)
        return value

    metadata = {
        "run_id": run_id,
        "created_at": now.isoformat(),
        "config": {key: _json_safe(value) for key, value in asdict(config).items()},
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    append_audit_event(
        run_dir / "logs" / "audit.jsonl",
        operator_id=config.operator_id,
        event="run_created",
        run_id=run_id,
        details={"mode": config.mode, "target_url": config.target_url or ""},
    )

    return run_dir


def _purge_old_run_dirs(run_root: Path, retention_days: int) -> None:
    if retention_days <= 0 or not run_root.exists():
        return
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    for child in run_root.iterdir():
        if not child.is_dir():
            continue
        ts = _parse_run_timestamp(child.name)
        if ts is None:
            continue
        if ts < cutoff:
            shutil.rmtree(child, ignore_errors=True)


def _parse_run_timestamp(run_id: str) -> datetime | None:
    # run_id format: YYYYMMDD_HHMMSS_<random>
    pieces = run_id.split("_")
    if len(pieces) < 3:
        return None
    stamp = f"{pieces[0]}_{pieces[1]}"
    try:
        parsed = datetime.strptime(stamp, "%Y%m%d_%H%M%S")
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC)
