"""HTTP execution engine with retries and request-cache deduplication."""

from __future__ import annotations

import hashlib
import http.client
import http.cookiejar
import json
import ssl
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib import error
from urllib import request as urllib_request

from llmmap.core.models import HttpRequest, HttpResponse


@dataclass(frozen=True)
class HttpExecutionOptions:
    timeout_seconds: float
    retries: int
    proxy: str | None
    verify_ssl: bool


TransportFn = Callable[[HttpRequest, HttpExecutionOptions], HttpResponse]


class RequestCache:
    """Simple in-memory request cache keyed by request fingerprint."""

    def __init__(self) -> None:
        self._items: dict[str, HttpResponse] = {}

    @staticmethod
    def fingerprint(req: HttpRequest) -> str:
        # Volatile headers are those that are often stripped or modified by the scanner/transport
        # but don't change the intent of the request for our caching purposes.
        volatile = {"content-length", "host", "connection", "accept-encoding", "user-agent"}
        filtered_headers = [
            (k, v) for k, v in req.headers.items()
            if k.lower() not in volatile
        ]

        fingerprint_data = {
            "method": req.method,
            "url": req.url,
            "headers": sorted(filtered_headers, key=lambda item: item[0].lower()),
            "body": req.body,
        }
        packed = json.dumps(fingerprint_data, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(packed.encode("utf-8")).hexdigest()

    def get(self, req: HttpRequest) -> HttpResponse | None:
        return self._items.get(self.fingerprint(req))

    def set(self, req: HttpRequest, resp: HttpResponse) -> None:
        self._items[self.fingerprint(req)] = resp


class HttpClient:
    """HTTP client with retry loop and response caching."""

    def __init__(
        self,
        options: HttpExecutionOptions,
        cache: RequestCache | None = None,
        transport: TransportFn | None = None,
    ) -> None:
        self._options = options
        self._cache = cache or RequestCache()
        self._cookie_jar = http.cookiejar.CookieJar()
        self._transport = transport or self._default_transport_impl
        self._request_count = 0
        self._count_lock = threading.Lock()
        self._opener = self._build_opener()

    @property
    def request_count(self) -> int:
        return self._request_count

    def seed_cache(self, req: HttpRequest, resp: HttpResponse) -> None:
        """Manually seed the cache with a known request/response pair."""
        self._cache.set(req, resp)

    def execute(self, req: HttpRequest, *, use_cache: bool = True) -> HttpResponse:
        from llmmap.core import dataflow
        if use_cache:
            cached = self._cache.get(req)
            if cached is not None:
                return HttpResponse(
                    status_code=cached.status_code,
                    headers=dict(cached.headers),
                    body=cached.body,
                    elapsed_ms=cached.elapsed_ms,
                    error=cached.error,
                    from_cache=True,
                )

        dataflow.log_http_request(req)
        last_response: HttpResponse | None = None
        attempts = max(1, self._options.retries + 1)
        for _ in range(attempts):
            response = self._transport(req, self._options)
            with self._count_lock:
                self._request_count += 1
            last_response = response
            if response.error is None:
                if use_cache:
                    self._cache.set(req, response)
                dataflow.log_http_response(req, response)
                return response

        assert last_response is not None
        dataflow.log_http_response(req, last_response)
        return last_response

    def _build_opener(self) -> urllib_request.OpenerDirector:
        handlers: list[urllib_request.BaseHandler] = []
        if self._options.proxy:
            handlers.append(
                urllib_request.ProxyHandler({
                    "http": self._options.proxy,
                    "https": self._options.proxy,
                })
            )

        if self._options.verify_ssl:
            context = ssl.create_default_context()
        else:
            context = ssl._create_unverified_context()  # noqa: SLF001

        handlers.append(urllib_request.HTTPSHandler(context=context))
        handlers.append(urllib_request.HTTPCookieProcessor(self._cookie_jar))
        return urllib_request.build_opener(*handlers)

    @staticmethod
    def _decompress(raw: bytes, headers: dict[str, str]) -> str:
        """Decompress response bytes according to Content-Encoding header."""
        import gzip
        import zlib

        encoding = ""
        for k, v in headers.items():
            if k.lower() == "content-encoding":
                encoding = v.strip().lower()
                break

        data = raw
        if encoding == "gzip" or encoding == "x-gzip":
            try:
                data = gzip.decompress(raw)
            except Exception:
                pass  # fall through to raw bytes
        elif encoding == "deflate":
            try:
                data = zlib.decompress(raw)
            except Exception:
                try:
                    data = zlib.decompress(raw, -zlib.MAX_WBITS)
                except Exception:
                    pass
        elif encoding == "br":
            try:
                import brotli  # type: ignore[import-not-found]
                data = brotli.decompress(raw)
            except ImportError:
                pass  # brotli not installed, fall through
            except Exception:
                pass

        return data.decode("utf-8", errors="replace")

    @staticmethod
    def _sanitize_accept_encoding(value: str) -> str:
        """Strip brotli (br) from Accept-Encoding — we support gzip/deflate only.

        Follows sqlmap's approach: brotli requires an external C library and
        most targets happily serve gzip instead.
        """
        import re
        sanitized = re.sub(
            r"(?i)(,\s*)br(\s*,)?",
            lambda m: "," if m.group(1) and m.group(2) else "",
            value,
        )
        sanitized = re.sub(r"(?i)^br(\s*,\s*)?", "", sanitized)
        sanitized = sanitized.strip().strip(",").strip()
        return sanitized or "gzip, deflate"

    def _default_transport_impl(
        self, req: HttpRequest, options: HttpExecutionOptions,
    ) -> HttpResponse:
        body_bytes = req.body.encode("utf-8") if req.body else None
        safe_headers = {}
        from urllib.parse import quote
        for k, v in req.headers.items():
            key_lower = k.lower()
            # Strip brotli from Accept-Encoding (we only decompress gzip/deflate)
            if key_lower == "accept-encoding":
                v = self._sanitize_accept_encoding(v)
            try:
                v.encode('latin-1')
                safe_headers[k] = v
            except UnicodeEncodeError:
                safe_headers[k] = quote(v)

        outgoing = urllib_request.Request(
            req.url,
            data=body_bytes,
            method=req.method,
            headers=safe_headers,
        )

        _MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB guard

        started = time.perf_counter()
        try:
            with self._opener.open(outgoing, timeout=options.timeout_seconds) as incoming:
                raw_bytes = incoming.read(_MAX_RESPONSE_BYTES)
                resp_headers = dict(incoming.headers.items())
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                body_text = self._decompress(raw_bytes, resp_headers)
                return HttpResponse(
                    status_code=int(incoming.status),
                    headers=resp_headers,
                    body=body_text,
                    elapsed_ms=elapsed_ms,
                    error=None,
                    from_cache=False,
                )
        except error.HTTPError as exc:
            raw_bytes = exc.read(_MAX_RESPONSE_BYTES) if exc.fp else b""
            exc_headers = dict(exc.headers.items()) if exc.headers else {}
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            body_text = self._decompress(raw_bytes, exc_headers) if raw_bytes else ""
            return HttpResponse(
                status_code=int(exc.code),
                headers=exc_headers,
                body=body_text,
                elapsed_ms=elapsed_ms,
                error=f"http_error:{exc.code}",
                from_cache=False,
            )
        except (error.URLError, TimeoutError) as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return HttpResponse(
                status_code=0,
                headers={},
                body="",
                elapsed_ms=elapsed_ms,
                error=str(exc),
                from_cache=False,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return HttpResponse(
                status_code=0,
                headers={},
                body="",
                elapsed_ms=elapsed_ms,
                error=f"transport_error:{type(exc).__name__}:{str(exc)}",
                from_cache=False,
            )
