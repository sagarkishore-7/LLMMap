from __future__ import annotations

from llmmap.core.models import HttpRequest, InjectionPoint
from llmmap.core.request_mutator import apply_prompt


def test_apply_prompt_in_query() -> None:
    req = HttpRequest(method="GET", url="https://example.com/?a=1&b=*", headers={}, body="")
    point = InjectionPoint(point_id="query:b:1", location="query", key="b", original_value="*")

    out = apply_prompt(req, point, "PAYLOAD", marker="*")
    assert "b=PAYLOAD" in out.url



def test_apply_prompt_in_body() -> None:
    req = HttpRequest(method="POST", url="https://example.com/", headers={}, body="x=1&m=*")
    point = InjectionPoint(point_id="body:m:1", location="body", key="m", original_value="*")

    out = apply_prompt(req, point, "PAYLOAD", marker="*")
    assert "m=PAYLOAD" in out.body



def test_apply_prompt_in_header_and_cookie() -> None:
    req = HttpRequest(
        method="GET",
        url="https://example.com/",
        headers={"X-Test": "prefix*", "Cookie": "sid=abc; tok=*"},
        body="",
    )

    header_point = InjectionPoint(
        point_id="header:X-Test",
        location="header",
        key="X-Test",
        original_value="prefix*",
    )
    cookie_point = InjectionPoint(
        point_id="cookie:tok:1",
        location="cookie",
        key="tok",
        original_value="*",
    )

    out_header = apply_prompt(req, header_point, "PAYLOAD", marker="*")
    assert out_header.headers["X-Test"] == "prefixPAYLOAD"

    out_cookie = apply_prompt(req, cookie_point, "PAYLOAD", marker="*")
    assert "tok=PAYLOAD" in out_cookie.headers["Cookie"]
