from __future__ import annotations

from pathlib import Path

from llmmap.config import RuntimeConfig
from llmmap.core.request_loader import load_request


def _base_config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        mode="dry",
        enabled_stages=("stage1", "stage2", "stage3"),
        target_url="https://example.com/path?x=1",
        run_root=tmp_path,
        request_file=None,
        method=None,
        param_filter=(),
        headers=(),
        cookies=(),
        data=None,
        marker="*",
        injection_points="QBHCP",
        scheme="https",
        timeout_seconds=10.0,
        retries=1,
        proxy=None,
        verify_ssl=False,
        prompt_dir=None,
        prompt_stage="stage1",
        prompt_families=(),
        prompt_tags=(),
        max_prompts=25,
        detector_threshold=0.6,
        fp_suppression=True,
        reliability_retries=5,
        confirm_threshold=3,
        match_regex=(),
        match_keywords=(),
        secret_hints=(),
        temperature_sweep=(),
        repro_check=False,
        oob_provider="none",
        interactsh_client_path="interactsh-client",
        interactsh_server=None,
        interactsh_token=None,
        oob_wait_seconds=10.0,
        oob_poll_interval=5,
    )



def test_load_structured_request(tmp_path: Path) -> None:
    config = _base_config(tmp_path)
    req = load_request(config)
    assert req.method == "GET"
    assert req.url == "https://example.com/path?x=1"
    assert req.body == ""



def test_load_raw_request_with_host_and_override(tmp_path: Path) -> None:
    raw_file = tmp_path / "request.txt"
    raw_file.write_text(
        "POST /api/chat?x=1 HTTP/1.1\n"
        "Host: vuln.example\n"
        "Content-Type: application/x-www-form-urlencoded\n"
        "\n"
        "message=hello*world\n",
        encoding="utf-8",
    )

    base = _base_config(tmp_path)
    config = RuntimeConfig(
        **{
            **base.__dict__,
            "target_url": None,
            "request_file": raw_file,
            "headers": ("X-Test: 1",),
            "cookies": ("sid=abc",),
        }
    )

    req = load_request(config)
    assert req.method == "POST"
    assert req.url == "https://vuln.example/api/chat?x=1"
    assert req.headers["X-Test"] == "1"
    assert "sid=abc" in req.headers["Cookie"]
    assert "hello*world" in req.body
