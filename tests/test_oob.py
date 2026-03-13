from __future__ import annotations

from pathlib import Path

from llmmap.core.oob import InteractshAdapter, generate_canary_token


def test_generate_canary_token_is_dns_safe_and_unique() -> None:
    token_a = generate_canary_token("run123", "rule_addition_prompting", "query:q:0")
    token_b = generate_canary_token("run123", "rule_addition_prompting", "query:q:0")

    assert token_a.startswith("lm")
    assert token_a.isalnum()
    assert token_a != token_b


def test_interactsh_adapter_bootstrap_and_poll(tmp_path: Path) -> None:
    outputs = [
        "",
        (
            '{"protocol":"dns","timestamp":"2026-03-06T12:00:00Z",'
            '"raw-request":"GET / lmabc123xyz.oast.test","remote-address":"1.2.3.4"}\n'
            '{"protocol":"http","timestamp":"2026-03-06T12:00:01Z",'
            '"raw-request":"GET / lmdef456uvw.oast.test","remote-address":"5.6.7.8"}\n'
        ),
    ]

    def fake_runner(cmd: list[str], timeout_seconds: int) -> str:
        if "-psf" in cmd:
            prompt_file = Path(cmd[cmd.index("-psf") + 1])
            prompt_file.write_text("oast.test\n", encoding="utf-8")
        return outputs.pop(0) if outputs else ""

    adapter = InteractshAdapter(
        client_path="interactsh-client",
        state_dir=tmp_path,
        server=None,
        token=None,
        poll_interval_seconds=5,
        runner=fake_runner,
    )

    host = adapter.bootstrap()
    assert host == "oast.test"
    assert adapter.callback_url("lmabc123xyz") == "https://oast.test/lmabc123xyz"

    events = adapter.poll_events({"lmabc123xyz", "missingtoken"}, wait_seconds=1.0)
    assert len(events) == 1
    assert events[0].token == "lmabc123xyz"
    assert events[0].protocol == "dns"
    assert events[0].remote_address == "1.2.3.4"
