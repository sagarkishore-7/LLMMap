"""Provider adapter implementations for LLM backends."""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, type] = {}


def get_adapter(provider: str, **kwargs: Any) -> Any:
    """Look up and instantiate a provider adapter by name."""
    cls = PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(
            f"unknown provider {provider!r}, "
            f"expected one of: {', '.join(sorted(PROVIDERS))}"
        )
    return cls(**kwargs)


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

class OllamaAdapter:
    """Adapter for Ollama's /api/chat endpoint."""

    def __init__(
        self, *, model: str, api_key: str | None = None, base_url: str | None = None,
    ) -> None:
        self._base_url = (base_url or "http://127.0.0.1:11434").rstrip("/")

    def build_request(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        temperature: float,
    ) -> tuple[str, bytes, dict[str, str]]:
        url = f"{self._base_url}/api/chat"
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }).encode()
        return url, body, {"Content-Type": "application/json"}

    def parse_response(self, raw: bytes) -> str:
        data = json.loads(raw.decode())
        content: str = data.get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError("empty response from Ollama")
        return content

    def check_connectivity(self, timeout: float = 3.0) -> bool:
        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return bool(resp.status == 200)
        except Exception:
            return False


PROVIDERS["ollama"] = OllamaAdapter


# ---------------------------------------------------------------------------
# OpenAI  (also works with vLLM, LMStudio, and other compatible servers)
# ---------------------------------------------------------------------------

class OpenAIAdapter:
    """Adapter for OpenAI /v1/chat/completions."""

    def __init__(
        self, *, model: str, api_key: str | None = None, base_url: str | None = None,
    ) -> None:
        self._base_url = (base_url or "https://api.openai.com").rstrip("/")
        self._api_key = api_key

    def build_request(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        temperature: float,
    ) -> tuple[str, bytes, dict[str, str]]:
        url = f"{self._base_url}/v1/chat/completions"
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
        }).encode()
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return url, body, headers

    def parse_response(self, raw: bytes) -> str:
        data = json.loads(raw.decode())
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("no choices in OpenAI response")
        content: str = choices[0].get("message", {}).get("content", "").strip()
        return content

    def check_connectivity(self, timeout: float = 3.0) -> bool:
        if self._api_key:
            return True
        try:
            req = urllib.request.Request(f"{self._base_url}/v1/models")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return bool(resp.status == 200)
        except Exception:
            return False


PROVIDERS["openai"] = OpenAIAdapter


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

class AnthropicAdapter:
    """Adapter for Anthropic /v1/messages.

    System prompt goes in a separate top-level ``system`` field, NOT in messages.
    """

    def __init__(
        self, *, model: str, api_key: str | None = None, base_url: str | None = None,
    ) -> None:
        self._base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self._api_key = api_key

    def build_request(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        temperature: float,
    ) -> tuple[str, bytes, dict[str, str]]:
        url = f"{self._base_url}/v1/messages"
        prompt: dict = {
            "model": model,
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": 2048,
            "temperature": temperature,
        }
        if system_prompt:
            prompt["system"] = system_prompt
        body = json.dumps(prompt).encode()
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if self._api_key:
            headers["x-api-key"] = self._api_key
        return url, body, headers

    def parse_response(self, raw: bytes) -> str:
        data = json.loads(raw.decode())
        content_blocks = data.get("content", [])
        if not content_blocks:
            raise ValueError("empty content in Anthropic response")
        parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
        return "".join(parts).strip()

    def check_connectivity(self, timeout: float = 3.0) -> bool:
        return bool(self._api_key)


PROVIDERS["anthropic"] = AnthropicAdapter


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

class GoogleAdapter:
    """Adapter for Google Gemini generateContent API.

    Auth via ``?key=`` query parameter.
    ``system_instruction`` is a top-level field separate from ``contents``.
    """

    def __init__(
        self, *, model: str, api_key: str | None = None, base_url: str | None = None,
    ) -> None:
        self._base_url = (
            base_url or "https://generativelanguage.googleapis.com"
        ).rstrip("/")
        self._api_key = api_key

    def build_request(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        temperature: float,
    ) -> tuple[str, bytes, dict[str, str]]:
        url = f"{self._base_url}/v1beta/models/{model}:generateContent"
        if self._api_key:
            url += f"?key={self._api_key}"
        prompt: dict = {
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_prompt:
            prompt["system_instruction"] = {"parts": [{"text": system_prompt}]}
        body = json.dumps(prompt).encode()
        return url, body, {"Content-Type": "application/json"}

    def parse_response(self, raw: bytes) -> str:
        data = json.loads(raw.decode())
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("no candidates in Google response")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()

    def check_connectivity(self, timeout: float = 3.0) -> bool:
        return bool(self._api_key)


PROVIDERS["google"] = GoogleAdapter
