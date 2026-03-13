from __future__ import annotations

from llmmap.core.injection_points import discover_injection_points
from llmmap.core.models import HttpRequest


def test_discover_marker_points() -> None:
    req = HttpRequest(
        method="POST",
        url="https://example.com/a*/b?q=1&x=*",
        headers={"X-Test": "aa*bb", "Cookie": "sid=123; tok=*"},
        body="message=hello*&other=value",
    )

    points = discover_injection_points(req, marker="*", injection_points="QBHCP")
    ids = {point.point_id for point in points}

    assert "query:x:1" in ids
    assert "body:message:0" in ids
    assert "header:X-Test" in ids
    assert "cookie:tok:1" in ids
    assert "path:marker:0" in ids



def test_discover_without_marker_falls_back_to_all_selected_vectors() -> None:
    req = HttpRequest(
        method="POST",
        url="https://example.com/path?q=1&x=2",
        headers={"X-Test": "abc"},
        body="message=hello&other=value",
    )

    points = discover_injection_points(req, marker="*", injection_points="QBH")
    ids = {point.point_id for point in points}

    assert "query:q:0" in ids
    assert "query:x:1" in ids
    assert "body:message:0" in ids
    assert "header:X-Test" in ids
