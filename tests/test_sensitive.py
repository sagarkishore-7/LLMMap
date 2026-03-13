from __future__ import annotations

from pathlib import Path

from llmmap.core.sensitive import purge_sensitive_artifacts


def test_purge_sensitive_artifacts_removes_known_files(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(parents=True)
    for name in ("pivot_trace.json", "oob_events.json", "tap_trace.json", "tap_events.json"):
        (artifacts / name).write_text("{}", encoding="utf-8")
    (artifacts / "summary.txt").write_text("keep", encoding="utf-8")

    removed = purge_sensitive_artifacts(tmp_path)

    assert set(removed) == {
        "artifacts/pivot_trace.json",
        "artifacts/oob_events.json",
        "artifacts/tap_trace.json",
        "artifacts/tap_events.json",
    }
    assert not (artifacts / "pivot_trace.json").exists()
    assert (artifacts / "summary.txt").exists()
