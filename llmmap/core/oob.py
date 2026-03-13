"""Week 7 OOB canary support using Interactsh client integration."""

from __future__ import annotations

import hashlib
import json
import re
import socketserver
import struct
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

_HOST_RE = re.compile(r"\b([a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+){2,})\b", re.IGNORECASE)


@dataclass(frozen=True)
class CanaryEvent:
    token: str
    protocol: str
    observed_at: str
    remote_address: str
    raw_line: str


Runner = Callable[[list[str], int], str]


def generate_canary_token(run_id: str, prompt_id: str, point_id: str) -> str:
    """Build a DNS-safe correlation token for a prompt-point request."""
    seed = f"{run_id}:{prompt_id}:{point_id}:{uuid4().hex}".encode()
    digest = hashlib.sha1(seed).hexdigest()[:24]
    return f"lm{digest}"


class InteractshAdapter:
    """Interactsh CLI-backed canary session manager and event poller."""

    def __init__(
        self,
        client_path: str,
        state_dir: Path,
        server: str | None,
        token: str | None,
        poll_interval_seconds: int,
        runner: Runner | None = None,
    ) -> None:
        self._client_path = client_path
        self._state_dir = state_dir
        self._server = server
        self._token = token
        self._poll_interval_seconds = max(1, poll_interval_seconds)
        self._runner = runner or _default_runner
        self._session_file = self._state_dir / "interactsh.session"
        self._prompt_file = self._state_dir / "interactsh_prompt.txt"
        self._base_domain: str | None = None

    def bootstrap(self) -> str | None:
        """Start/load an Interactsh session and fetch one generated prompt domain."""
        if self._base_domain is not None:
            return self._base_domain

        self._state_dir.mkdir(parents=True, exist_ok=True)
        cmd = self._base_command() + [
            "-n",
            "1",
            "-ps",
            "-psf",
            str(self._prompt_file),
        ]
        output = self._runner(cmd, self._poll_interval_seconds + 2)

        prompt_domain = self._read_prompt_domain()
        if prompt_domain is None:
            prompt_domain = _extract_host_from_text(output)
        self._base_domain = prompt_domain
        return prompt_domain

    def callback_url(self, token: str) -> str | None:
        if self._base_domain is None:
            return None
        return f"https://{self._base_domain}/{token}"

    def callback_host(self) -> str | None:
        return self._base_domain

    def poll_events(self, tokens: set[str], wait_seconds: float) -> list[CanaryEvent]:
        if not tokens:
            return []
        if self._base_domain is None:
            return []

        cmd = self._base_command()
        timeout_seconds = max(1, int(wait_seconds) + self._poll_interval_seconds + 2)
        output = self._runner(cmd, timeout_seconds)
        return _extract_events(tokens, output)

    def _read_prompt_domain(self) -> str | None:
        if not self._prompt_file.exists():
            return None
        for line in self._prompt_file.read_text(encoding="utf-8").splitlines():
            candidate = line.strip().lower()
            if not candidate:
                continue
            if "." in candidate and " " not in candidate:
                return candidate
        return None

    def _base_command(self) -> list[str]:
        cmd = [
            self._client_path,
            "-json",
            "-pi",
            str(self._poll_interval_seconds),
            "-sf",
            str(self._session_file),
        ]
        if self._server:
            cmd.extend(["-server", self._server])
        if self._token:
            cmd.extend(["-t", self._token])
        return cmd


class BuiltinCanaryAdapter:
    """Built-in OOB listener using local HTTP and DNS endpoints."""

    def __init__(self, host: str, http_port: int, dns_port: int = 53535) -> None:
        self._host = host
        self._http_port = http_port
        self._dns_port = dns_port
        self._events: list[CanaryEvent] = []
        self._lock = threading.Lock()
        self._http_server: ThreadingHTTPServer | None = None
        self._dns_server: socketserver.ThreadingUDPServer | None = None
        self._started = False

    def bootstrap(self) -> str | None:
        if self._started:
            return f"{self._host}:{self._http_port}"
        self._start_http()
        self._start_dns()
        self._started = True
        return f"{self._host}:{self._http_port}"

    def callback_url(self, token: str) -> str | None:
        return f"http://{self._host}:{self._http_port}/cb/{token}"

    def callback_host(self) -> str | None:
        return f"{self._host}:{self._http_port}"

    def poll_events(self, tokens: set[str], wait_seconds: float) -> list[CanaryEvent]:
        if wait_seconds > 0:
            threading.Event().wait(wait_seconds)
        with self._lock:
            matched = [event for event in self._events if event.token in tokens]
        dedup: dict[tuple[str, str, str, str], CanaryEvent] = {}
        for event in matched:
            key = (event.token, event.protocol, event.observed_at, event.remote_address)
            dedup[key] = event
        return list(dedup.values())

    def _start_http(self) -> None:
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                token = self.path.strip("/").split("/")[-1]
                parent._add_event(
                    token=token,
                    protocol="http",
                    remote=self.client_address[0],
                    raw=self.path,
                )
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        self._http_server = ThreadingHTTPServer((self._host, self._http_port), Handler)
        thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        thread.start()

    def _start_dns(self) -> None:
        parent = self

        class DnsHandler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                data, sock = self.request
                token = _extract_dns_token(data)
                if token:
                    parent._add_event(
                        token=token,
                        protocol="dns",
                        remote=self.client_address[0],
                        raw=f"dns:{token}",
                    )
                response = _build_dns_nxdomain(data)
                sock.sendto(response, self.client_address)

        self._dns_server = socketserver.ThreadingUDPServer((self._host, self._dns_port), DnsHandler)
        thread = threading.Thread(target=self._dns_server.serve_forever, daemon=True)
        thread.start()

    def _add_event(self, token: str, protocol: str, remote: str, raw: str) -> None:
        if not token or len(token) < 4:
            return
        event = CanaryEvent(
            token=token,
            protocol=protocol,
            observed_at=datetime.now(UTC).isoformat(),
            remote_address=remote,
            raw_line=raw,
        )
        with self._lock:
            self._events.append(event)


def _default_runner(cmd: list[str], timeout_seconds: int) -> str:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
        return (completed.stdout or "") + "\n" + (completed.stderr or "")
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_timeout_text(exc.stdout)
        stderr = _coerce_timeout_text(exc.stderr)
        return stdout + "\n" + stderr
    except OSError:
        return ""


def _coerce_timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _extract_host_from_text(text: str) -> str | None:
    for match in _HOST_RE.finditer(text):
        candidate = match.group(1).lower()
        if candidate.startswith("projectdiscovery."):
            continue
        return candidate
    return None


def _extract_events(tokens: set[str], output: str) -> list[CanaryEvent]:
    token_map = {token.lower(): token for token in tokens}
    seen: set[tuple[str, str, str, str]] = set()
    events: list[CanaryEvent] = []

    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue

        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            parsed = {"line": line}

        blob = json.dumps(parsed, sort_keys=True).lower()
        for token_lower, original_token in token_map.items():
            if token_lower not in blob:
                continue
            protocol = _infer_protocol(parsed, blob)
            observed = _infer_observed_at(parsed)
            remote = _infer_remote_address(parsed)
            key = (original_token, protocol, observed, remote)
            if key in seen:
                continue
            seen.add(key)
            events.append(
                CanaryEvent(
                    token=original_token,
                    protocol=protocol,
                    observed_at=observed,
                    remote_address=remote,
                    raw_line=line,
                )
            )
    return events


def _infer_protocol(parsed: dict[str, object], blob: str) -> str:
    text = " ".join(
        [
            str(parsed.get("protocol", "")),
            str(parsed.get("type", "")),
            str(parsed.get("q-type", "")),
            blob,
        ]
    ).lower()
    if "http" in text:
        return "http"
    if "dns" in text:
        return "dns"
    if "smtp" in text:
        return "smtp"
    if "ldap" in text:
        return "ldap"
    return "unknown"


def _infer_observed_at(parsed: dict[str, object]) -> str:
    for key in ("timestamp", "time", "created", "created_at"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return datetime.now(UTC).isoformat()


def _infer_remote_address(parsed: dict[str, object]) -> str:
    for key in ("remote-address", "remote_address", "remote-ip", "remote_ip", "ip"):
        value = parsed.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def _extract_dns_token(packet: bytes) -> str | None:
    if len(packet) < 12:
        return None
    idx = 12
    labels: list[str] = []
    while idx < len(packet):
        length = packet[idx]
        idx += 1
        if length == 0:
            break
        if idx + length > len(packet):
            return None
        label = packet[idx : idx + length].decode("ascii", errors="ignore")
        labels.append(label.lower())
        idx += length
    for label in labels:
        if label.startswith("lm") and len(label) >= 10:
            return label
    return labels[0] if labels else None


def _build_dns_nxdomain(request: bytes) -> bytes:
    if len(request) < 12:
        return b""
    txid = request[:2]
    flags = struct.pack("!H", 0x8183)
    counts = struct.pack("!HHHH", 1, 0, 0, 0)
    question = request[12:]
    return txid + flags + counts + question
