"""Tests for the unified LLM client and provider adapters."""

from __future__ import annotations

import json

import pytest

from llmmap.llm.client import LLMClient
from llmmap.llm.providers import (
    PROVIDERS,
    AnthropicAdapter,
    GoogleAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    get_adapter,
)

# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

def test_providers_registered() -> None:
    assert sorted(PROVIDERS.keys()) == ["anthropic", "google", "ollama", "openai"]


def test_get_adapter_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        get_adapter("nonexistent", model="x")


# ---------------------------------------------------------------------------
# OllamaAdapter
# ---------------------------------------------------------------------------

class TestOllamaAdapter:
    def _adapter(self) -> OllamaAdapter:
        return OllamaAdapter(model="dolphin3:8b")

    def test_build_request_url(self) -> None:
        url, body, headers = self._adapter().build_request(
            model="dolphin3:8b",
            system_prompt="sys",
            user_message="usr",
            temperature=0.5,
        )
        assert url == "http://127.0.0.1:11434/api/chat"
        data = json.loads(body)
        assert data["model"] == "dolphin3:8b"
        assert data["stream"] is False
        assert data["options"]["temperature"] == 0.5
        assert data["messages"][0] == {"role": "system", "content": "sys"}
        assert data["messages"][1] == {"role": "user", "content": "usr"}

    def test_build_request_custom_base_url(self) -> None:
        adapter = OllamaAdapter(model="m", base_url="http://myhost:9999")
        url, _, _ = adapter.build_request("m", "s", "u", 0.0)
        assert url == "http://myhost:9999/api/chat"

    def test_parse_response(self) -> None:
        raw = json.dumps({"message": {"content": "hello world"}}).encode()
        assert self._adapter().parse_response(raw) == "hello world"

    def test_parse_response_empty_raises(self) -> None:
        raw = json.dumps({"message": {"content": ""}}).encode()
        with pytest.raises(ValueError, match="empty"):
            self._adapter().parse_response(raw)

    def test_check_connectivity_unreachable(self) -> None:
        adapter = OllamaAdapter(model="m", base_url="http://127.0.0.1:65432")
        assert adapter.check_connectivity(timeout=0.5) is False


# ---------------------------------------------------------------------------
# OpenAIAdapter
# ---------------------------------------------------------------------------

class TestOpenAIAdapter:
    def _adapter(self, **kw: object) -> OpenAIAdapter:
        return OpenAIAdapter(model="gpt-4o-mini", api_key="sk-test", **kw)

    def test_build_request_format(self) -> None:
        url, body, headers = self._adapter().build_request(
            model="gpt-4o-mini",
            system_prompt="sys",
            user_message="usr",
            temperature=0.0,
        )
        assert url == "https://api.openai.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer sk-test"
        data = json.loads(body)
        assert data["model"] == "gpt-4o-mini"
        assert data["temperature"] == 0.0
        assert len(data["messages"]) == 2

    def test_build_request_custom_base_url(self) -> None:
        adapter = OpenAIAdapter(model="m", base_url="http://localhost:8000")
        url, _, headers = adapter.build_request("m", "s", "u", 0.0)
        assert url == "http://localhost:8000/v1/chat/completions"
        assert "Authorization" not in headers  # no api key

    def test_parse_response(self) -> None:
        raw = json.dumps({
            "choices": [{"message": {"content": "answer"}}]
        }).encode()
        assert self._adapter().parse_response(raw) == "answer"

    def test_parse_response_no_choices_raises(self) -> None:
        raw = json.dumps({"choices": []}).encode()
        with pytest.raises(ValueError, match="no choices"):
            self._adapter().parse_response(raw)

    def test_check_connectivity_with_key(self) -> None:
        assert self._adapter().check_connectivity() is True

    def test_check_connectivity_no_key_unreachable(self) -> None:
        adapter = OpenAIAdapter(model="m", base_url="http://127.0.0.1:65432")
        assert adapter.check_connectivity(timeout=0.5) is False


# ---------------------------------------------------------------------------
# AnthropicAdapter
# ---------------------------------------------------------------------------

class TestAnthropicAdapter:
    def _adapter(self) -> AnthropicAdapter:
        return AnthropicAdapter(model="claude-sonnet-4-20250514", api_key="sk-ant-test")

    def test_build_request_system_not_in_messages(self) -> None:
        url, body, headers = self._adapter().build_request(
            model="claude-sonnet-4-20250514",
            system_prompt="be a judge",
            user_message="evaluate this",
            temperature=0.0,
        )
        assert url == "https://api.anthropic.com/v1/messages"
        assert headers["x-api-key"] == "sk-ant-test"
        assert headers["anthropic-version"] == "2023-06-01"
        data = json.loads(body)
        # System prompt must be top-level, NOT in messages
        assert data["system"] == "be a judge"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"
        assert data["max_tokens"] == 2048

    def test_parse_response(self) -> None:
        raw = json.dumps({
            "content": [{"type": "text", "text": "result"}]
        }).encode()
        assert self._adapter().parse_response(raw) == "result"

    def test_parse_response_empty_raises(self) -> None:
        raw = json.dumps({"content": []}).encode()
        with pytest.raises(ValueError, match="empty content"):
            self._adapter().parse_response(raw)

    def test_check_connectivity_with_key(self) -> None:
        assert self._adapter().check_connectivity() is True

    def test_check_connectivity_no_key(self) -> None:
        adapter = AnthropicAdapter(model="m")
        assert adapter.check_connectivity() is False


# ---------------------------------------------------------------------------
# GoogleAdapter
# ---------------------------------------------------------------------------

class TestGoogleAdapter:
    def _adapter(self) -> GoogleAdapter:
        return GoogleAdapter(model="gemini-2.0-flash", api_key="test-key")

    def test_build_request_format(self) -> None:
        url, body, headers = self._adapter().build_request(
            model="gemini-2.0-flash",
            system_prompt="sys",
            user_message="usr",
            temperature=0.0,
        )
        assert "gemini-2.0-flash:generateContent" in url
        assert "?key=test-key" in url
        data = json.loads(body)
        assert data["system_instruction"] == {"parts": [{"text": "sys"}]}
        assert data["contents"] == [{"parts": [{"text": "usr"}]}]
        assert data["generationConfig"]["temperature"] == 0.0

    def test_parse_response(self) -> None:
        raw = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "output"}]}}]
        }).encode()
        assert self._adapter().parse_response(raw) == "output"

    def test_parse_response_no_candidates_raises(self) -> None:
        raw = json.dumps({"candidates": []}).encode()
        with pytest.raises(ValueError, match="no candidates"):
            self._adapter().parse_response(raw)

    def test_check_connectivity_with_key(self) -> None:
        assert self._adapter().check_connectivity() is True

    def test_check_connectivity_no_key(self) -> None:
        adapter = GoogleAdapter(model="m")
        assert adapter.check_connectivity() is False


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

def test_llm_client_repr() -> None:
    client = LLMClient(provider="ollama", model="dolphin3:8b")
    assert "ollama" in repr(client)
    assert "dolphin3:8b" in repr(client)
