"""Unified LLM client with pluggable provider backends."""

from __future__ import annotations

import logging
import threading
import urllib.request

LOGGER = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when an LLM call fails."""


class LLMClient:
    """Provider-agnostic LLM chat interface.

    Usage::

        client = LLMClient(provider="openai", model="gpt-4o-mini", api_key="sk-...")
        answer = client.chat("You are a judge.", "Is this a prompt injection?")

    LLM calls are serialized with a lock so that concurrent threads
    (e.g. from ThreadPoolExecutor) do not overload backends like Ollama
    that process requests serially — queued requests would timeout and
    fall back to the weaker heuristic judge.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider_name = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self._lock = threading.Lock()

        from llmmap.llm.providers import get_adapter

        self._adapter = get_adapter(
            provider, model=model, api_key=api_key, base_url=base_url,
        )

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.0,
        timeout: float = 60.0,
        _df_component: str = "llm",
        _df_technique: str = "",
    ) -> str:
        """Send a chat message and return the assistant's response text.

        Raises ``LLMError`` on failure.
        """
        from llmmap.core import dataflow
        dataflow.log_llm_request(
            component=_df_component,
            provider=self.provider_name,
            model=self.model,
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            technique=_df_technique,
        )

        url, body, headers = self._adapter.build_request(
            model=self.model,
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
        )
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        # Serialize LLM calls — prevents timeout cascades when the backend
        # (e.g. Ollama) processes requests serially.
        with self._lock:
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read()
            except Exception as exc:
                raise LLMError(f"{self.provider_name} request failed: {exc}") from exc

            try:
                result = self._adapter.parse_response(raw)
            except Exception as exc:
                raise LLMError(
                    f"{self.provider_name} response parse failed: {exc}"
                ) from exc

        dataflow.log_llm_response(
            component=_df_component,
            provider=self.provider_name,
            model=self.model,
            response_text=result,
            technique=_df_technique,
        )
        return str(result)

    def check_connectivity(self, timeout: float = 3.0) -> bool:
        """Return True if the configured backend is reachable / configured."""
        return bool(self._adapter.check_connectivity(timeout))

    def __repr__(self) -> str:
        return f"LLMClient(provider={self.provider_name!r}, model={self.model!r})"
