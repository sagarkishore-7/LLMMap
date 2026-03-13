"""Data-flow trace logger.

When enabled (--data-flow), every inter-component data transfer is written
as a JSON line to  <run_dir>/dataflow.jsonl:

  HTTP  OUT → request  sent to target
  HTTP  IN  → response received from target
  LLM   OUT → prompt   sent to LLM backend
  LLM   IN  → reply    received from LLM backend

Enable via ``init(path)``; all other modules call ``log_*`` helpers which
are no-ops when the logger is not initialised.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llmmap.core.models import HttpRequest, HttpResponse


# ── singleton ─────────────────────────────────────────────────────────────────

class _DataFlowLogger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._f = path.open("a", encoding="utf-8")
        self._lock = threading.Lock()

    def _write(self, record: dict) -> None:
        record.setdefault("ts", time.strftime("%H:%M:%S"))
        line = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._f.write(line + "\n")
            self._f.flush()

    def http_request(self, req: HttpRequest) -> None:
        self._write({
            "direction": "OUT",
            "component": "http",
            "event": "request",
            "method": req.method,
            "url": req.url,
            "headers": dict(req.headers),
            "body": req.body or "",
        })

    def http_response(self, req: HttpRequest, resp: HttpResponse) -> None:
        self._write({
            "direction": "IN",
            "component": "http",
            "event": "response",
            "url": req.url,
            "status_code": resp.status_code,
            "elapsed_ms": round(resp.elapsed_ms, 2),
            "body": resp.body or "",
            "error": resp.error or "",
        })

    def llm_request(
        self,
        component: str,
        provider: str,
        model: str,
        system_prompt: str,
        user_message: str,
        temperature: float,
        technique: str = "",
    ) -> None:
        record: dict = {
            "direction": "OUT",
            "component": component,
            "event": "llm_request",
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "system_prompt": system_prompt,
            "user_message": user_message,
        }
        if technique:
            record["technique"] = technique
        self._write(record)

    def llm_response(
        self,
        component: str,
        provider: str,
        model: str,
        response_text: str,
        technique: str = "",
    ) -> None:
        record: dict = {
            "direction": "IN",
            "component": component,
            "event": "llm_response",
            "provider": provider,
            "model": model,
            "response": response_text,
        }
        if technique:
            record["technique"] = technique
        self._write(record)

    def close(self) -> None:
        with self._lock:
            self._f.close()


_instance: _DataFlowLogger | None = None


def init(path: Path) -> None:
    """Initialise the data-flow logger. Call once from the orchestrator."""
    global _instance
    _instance = _DataFlowLogger(path)


def get() -> _DataFlowLogger | None:
    return _instance


# ── convenience helpers (no-op when not initialised) ─────────────────────────

def log_http_request(req: HttpRequest) -> None:
    if _instance:
        _instance.http_request(req)


def log_http_response(req: HttpRequest, resp: HttpResponse) -> None:
    if _instance:
        _instance.http_response(req, resp)


def log_llm_request(
    component: str,
    provider: str,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.0,
    technique: str = "",
) -> None:
    if _instance:
        _instance.llm_request(
            component, provider, model, system_prompt,
            user_message, temperature, technique,
        )


def log_llm_response(
    component: str,
    provider: str,
    model: str,
    response_text: str,
    technique: str = "",
) -> None:
    if _instance:
        _instance.llm_response(component, provider, model, response_text, technique)
