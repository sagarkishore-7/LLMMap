"""HTTP request loading from raw request files and structured CLI options."""

from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit

from llmmap.config import RuntimeConfig
from llmmap.core.models import HttpRequest


class RequestLoadError(ValueError):
    """Raised when request input cannot be parsed."""



def _parse_header_values(raw_headers: tuple[str, ...]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for value in raw_headers:
        if ":" not in value:
            raise RequestLoadError(f"invalid --header value: {value!r}")
        key, header_val = value.split(":", 1)
        headers[key.strip()] = header_val.strip()
    return headers



def _merge_cookies(headers: dict[str, str], cookies: tuple[str, ...]) -> dict[str, str]:
    if not cookies:
        return headers

    merged = dict(headers)
    cookie_line = "; ".join(cookie.strip() for cookie in cookies if cookie.strip())
    if not cookie_line:
        return merged

    if "Cookie" in merged and merged["Cookie"].strip():
        merged["Cookie"] = f"{merged['Cookie']}; {cookie_line}"
    else:
        merged["Cookie"] = cookie_line

    return merged



def _compose_url(target_url: str | None, scheme: str, host: str | None, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path

    if target_url:
        parts = urlsplit(target_url)
        if parts.scheme and parts.netloc:
            base = f"{parts.scheme}://{parts.netloc}"
            return urljoin(base, path)

    if host:
        return f"{scheme}://{host}{path}"

    raise RequestLoadError("unable to compose URL: provide --target-url or Host header")



def _load_raw_request(config: RuntimeConfig) -> HttpRequest:
    if config.request_file is None:
        raise RequestLoadError("internal error: missing request file")

    raw = config.request_file.read_text(encoding="utf-8")
    
    # Check if it's a Burp Suite XML export
    burp_url = None
    if raw.strip().startswith("<?xml") or raw.strip().startswith("<items>"):
        try:
            root = ET.fromstring(raw)
            item = root.find("item")
            if item is not None:
                url_elem = item.find("url")
                if url_elem is not None and url_elem.text:
                    burp_url = url_elem.text.strip()
                req_elem = item.find("request")
                if req_elem is not None and req_elem.text:
                    text = req_elem.text.strip()
                    if req_elem.get("base64") == "true":
                        raw = base64.b64decode(text).decode("utf-8", errors="replace")
                    else:
                        raw = text
        except Exception:
            pass # fall back to normal parsing if XML is malformed

    # Detect line ending style used in the raw request (CRLF vs LF)
    # and preserve it — multipart bodies REQUIRE \r\n per RFC 2046.
    line_sep = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(line_sep)
    if not lines:
        raise RequestLoadError("raw request file is empty")

    request_line = lines[0].strip()
    line_parts = request_line.split()
    if len(line_parts) < 2:
        raise RequestLoadError(f"invalid request line: {request_line!r}")

    method = line_parts[0].upper()
    path = line_parts[1]

    header_lines: list[str] = []
    body_start_idx: int | None = None

    for i, line in enumerate(lines[1:], start=1):
        if not line.strip():
            body_start_idx = i + 1
            break
        header_lines.append(line)

    headers = _parse_header_values(tuple(header_lines))
    headers = _merge_cookies(headers, config.cookies)

    if config.headers:
        headers.update(_parse_header_values(config.headers))

    # Preserve the raw body with original line endings intact
    body = line_sep.join(lines[body_start_idx:]) if body_start_idx is not None else ""
    if config.data is not None:
        body = config.data

    if burp_url and not config.target_url:
        # The XML already has the full URL
        url = burp_url
    else:
        url = _compose_url(config.target_url, config.scheme, headers.get("Host"), path)

    return HttpRequest(method=method, url=url, headers=headers, body=body)



def _load_structured_request(config: RuntimeConfig) -> HttpRequest:
    if not config.target_url:
        raise RequestLoadError("structured mode requires --target-url")

    headers = _parse_header_values(config.headers)
    headers = _merge_cookies(headers, config.cookies)

    method = (config.method or ("POST" if config.data else "GET")).upper()
    body = config.data or ""

    return HttpRequest(method=method, url=config.target_url, headers=headers, body=body)



def load_request(config: RuntimeConfig) -> HttpRequest:
    """Load a normalized request from raw file or CLI fields."""
    if config.request_file is not None:
        return _load_raw_request(config)
    return _load_structured_request(config)

