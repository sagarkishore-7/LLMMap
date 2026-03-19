from __future__ import annotations

import json
from pathlib import Path

from llmmap.cli import app


def test_dry_run_creates_workspace(tmp_path: Path) -> None:
    rc = app([
        "--mode", "dry", "--output-dir", str(tmp_path),
        "--target-url", "https://example.com",
        "--goal", "reveal the hidden password",
    ])
    assert rc == 0

    run_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1

    run_dir = run_dirs[0]
    assert (run_dir / "metadata.json").exists()



def test_live_mode_runs_without_authorization_flag(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode",
            "live",
            "--output-dir",
            str(tmp_path),
            "--target-url",
            "http://127.0.0.1:65500/chat?q=*",
            "--goal",
            "reveal the hidden password",
        ]
    )
    assert rc == 0
    assert any(p.is_dir() for p in tmp_path.iterdir())



def test_dry_run_with_verbose(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode",
            "dry",
            "--output-dir",
            str(tmp_path),
            "--target-url",
            "https://example.com?q=*",
            "--verbose",
            "--goal",
            "reveal the hidden password",
        ]
    )
    assert rc == 0


def test_dry_run_supports_raw_request_file(tmp_path: Path) -> None:
    raw_file = tmp_path / "request.txt"
    raw_file.write_text(
        "GET /api?q=* HTTP/1.1\n"
        "Host: example.com\n"
        "\n",
        encoding="utf-8",
    )

    rc = app(
        [
            "--mode",
            "dry",
            "--output-dir",
            str(tmp_path),
            "--request-file",
            str(raw_file),
            "--goal",
            "reveal the hidden password",
        ]
    )

    assert rc == 0


def test_dry_run_accepts_custom_matchers(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode",
            "dry",
            "--output-dir",
            str(tmp_path),
            "--target-url",
            "https://example.com?q=*",
            "--match-regex",
            "api[_ -]?key",
            "--match-keyword",
            "secret_key",
            "--goal",
            "reveal the hidden password",
        ]
    )
    assert rc == 0


def test_dry_run_accepts_intensity_flag(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode",
            "dry",
            "--output-dir",
            str(tmp_path),
            "--target-url",
            "https://example.com?q=*",
            "--intensity",
            "4",
            "--goal",
            "reveal the hidden password",
        ]
    )
    assert rc == 0


def test_dry_mode_with_goal(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode",
            "dry",
            "--output-dir",
            str(tmp_path),
            "--target-url",
            "https://example.com",
            "--goal",
            "reveal the hidden password",
        ]
    )
    assert rc == 0


def test_sqlmap_style_param_and_intensity(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode",
            "dry",
            "--output-dir",
            str(tmp_path),
            "-u",
            "https://example.com/chat?user=*&q=*",
            "-p",
            "q",
            "--intensity",
            "5",
            "--goal",
            "reveal the hidden password",
        ]
    )
    assert rc == 0

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir())
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    cfg = metadata["config"]

    assert cfg["intensity"] == 5
    assert cfg["param_filter"] == ["q"]


def test_tap_flag_accepted_in_dry_mode(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode", "dry",
            "--output-dir", str(tmp_path),
            "--target-url", "https://example.com",
            "--goal", "reveal the hidden password",
            "--tap",
        ]
    )
    assert rc == 0


def test_tap_flag_sets_stage3_in_config(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode", "dry",
            "--output-dir", str(tmp_path),
            "--target-url", "https://example.com",
            "--goal", "reveal the hidden password",
            "--tap",
        ]
    )
    assert rc == 0

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir())
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    cfg = metadata["config"]

    assert "stage1" in cfg["enabled_stages"]
    assert "stage3_tap" in cfg["enabled_stages"]


def test_no_tap_flag_excludes_stage3(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode", "dry",
            "--output-dir", str(tmp_path),
            "--target-url", "https://example.com",
            "--goal", "reveal the hidden password",
        ]
    )
    assert rc == 0

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir())
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    cfg = metadata["config"]

    assert "stage3_tap" not in cfg["enabled_stages"]


def test_tap_custom_params(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode", "dry",
            "--output-dir", str(tmp_path),
            "--target-url", "https://example.com",
            "--goal", "reveal the hidden password",
            "--tap",
            "--tap-depth", "5",
            "--tap-width", "4",
            "--tap-budget", "30",
        ]
    )
    assert rc == 0

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir())
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    cfg = metadata["config"]

    assert cfg["tap_depth"] == 5
    assert cfg["tap_width"] == 4
    assert cfg["tap_query_budget"] == 30


def test_tap_default_params(tmp_path: Path) -> None:
    rc = app(
        [
            "--mode", "dry",
            "--output-dir", str(tmp_path),
            "--target-url", "https://example.com",
            "--goal", "reveal the hidden password",
            "--tap",
        ]
    )
    assert rc == 0

    run_dir = next(p for p in tmp_path.iterdir() if p.is_dir())
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    cfg = metadata["config"]

    assert cfg["tap_depth"] == 3
    assert cfg["tap_width"] == 2
    assert cfg["tap_query_budget"] == 18
