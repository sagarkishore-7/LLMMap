from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmmap.config import RuntimeConfig
from llmmap.core.run import create_run_workspace


def _config(
    run_root: Path,
    *,
    retention_days: int = 0,
    purge_old_runs: bool = False,
) -> RuntimeConfig:
    return RuntimeConfig(
        mode="dry",
        enabled_stages=("stage1", "stage2", "stage3"),
        target_url="https://example.com",
        run_root=run_root,
        request_file=None,
        method=None,
        param_filter=(),
        headers=(),
        cookies=(),
        data=None,
        marker="*",
        injection_points="QBHCP",
        scheme="https",
        timeout_seconds=5.0,
        retries=0,
        proxy=None,
        verify_ssl=False,
        prompt_dir=None,
        prompt_stage="stage1",
        prompt_families=(),
        prompt_tags=(),
        max_prompts=2,
        detector_threshold=0.6,
        fp_suppression=True,
        reliability_retries=1,
        confirm_threshold=1,
        match_regex=(),
        match_keywords=(),
        secret_hints=(),
        temperature_sweep=(),
        repro_check=False,
        oob_provider="none",
        interactsh_client_path="interactsh-client",
        interactsh_server=None,
        interactsh_token=None,
        oob_wait_seconds=1.0,
        oob_poll_interval=1,
        operator_id="tester",
        retention_days=retention_days,
        purge_old_runs=purge_old_runs,
    )


def test_create_run_workspace_writes_audit_event(tmp_path: Path) -> None:
    run_dir = create_run_workspace(_config(tmp_path))
    audit_file = run_dir / "logs" / "audit.jsonl"
    assert audit_file.exists()
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    assert lines
    event = json.loads(lines[0])
    assert event["operator_id"] == "tester"
    assert event["event"] == "run_created"
    assert event["run_id"] == run_dir.name


def test_create_run_workspace_purges_old_runs(tmp_path: Path) -> None:
    old_stamp = (datetime.now(UTC) - timedelta(days=10)).strftime("%Y%m%d_%H%M%S")
    old_dir = tmp_path / f"{old_stamp}_oldrun00"
    old_dir.mkdir(parents=True)
    (old_dir / "metadata.json").write_text("{}", encoding="utf-8")

    fresh_stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    fresh_dir = tmp_path / f"{fresh_stamp}_newrun00"
    fresh_dir.mkdir(parents=True)
    (fresh_dir / "metadata.json").write_text("{}", encoding="utf-8")

    _ = create_run_workspace(_config(tmp_path, retention_days=3, purge_old_runs=True))

    assert not old_dir.exists()
    assert fresh_dir.exists()
