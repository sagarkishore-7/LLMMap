from __future__ import annotations

from llmmap.core.http_client import HttpClient, HttpExecutionOptions
from llmmap.core.models import HttpRequest, HttpResponse


def test_http_client_uses_cache_for_duplicate_request() -> None:
    calls = {"count": 0}

    def fake_transport(req: HttpRequest, options: HttpExecutionOptions) -> HttpResponse:
        calls["count"] += 1
        return HttpResponse(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            body=f"ok:{req.url}",
            elapsed_ms=1.2,
            error=None,
            from_cache=False,
        )

    client = HttpClient(
        options=HttpExecutionOptions(timeout_seconds=5.0, retries=1, proxy=None, verify_ssl=False),
        transport=fake_transport,
    )
    req = HttpRequest(method="GET", url="https://example.com", headers={}, body="")

    first = client.execute(req)
    second = client.execute(req)

    assert calls["count"] == 1
    assert first.from_cache is False
    assert second.from_cache is True



def test_http_client_retries_then_returns_last_error() -> None:
    calls = {"count": 0}

    def fake_transport(req: HttpRequest, options: HttpExecutionOptions) -> HttpResponse:
        calls["count"] += 1
        return HttpResponse(
            status_code=0,
            headers={},
            body="",
            elapsed_ms=2.0,
            error="network_error",
            from_cache=False,
        )

    client = HttpClient(
        options=HttpExecutionOptions(timeout_seconds=5.0, retries=2, proxy=None, verify_ssl=False),
        transport=fake_transport,
    )
    req = HttpRequest(method="GET", url="https://example.com", headers={}, body="")

    resp = client.execute(req)

    assert calls["count"] == 3
    assert resp.error == "network_error"
