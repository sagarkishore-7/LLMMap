from __future__ import annotations

from llmmap.core.orchestrator import _augment_with_secret_hints


def test_augment_with_secret_hints_appends_focus_clause() -> None:
    prompt = "Summarize context."
    updated = _augment_with_secret_hints(prompt, ("api_key", "secret_key"))
    assert "api_key" in updated
    assert "secret_key" in updated
    assert updated.startswith(prompt)


def test_augment_with_secret_hints_noop_without_hints() -> None:
    prompt = "Summarize context."
    assert _augment_with_secret_hints(prompt, ()) == prompt
