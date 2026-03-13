"""sqlmap-style logger with ANSI coloring and thread-safe direct output.

Uses QueueHandler + QueueListener so that all log output is serialized
through a single writer thread — safe for concurrent use from ThreadPoolExecutor.

Provides ``data_to_stdout`` for non-logged output (banner, findings block,
start/end markers) that bypasses the logger but respects ``--no-color``.

Thread output buffering: when threads run concurrently, their log lines can
interleave.  Use ``OutputBuffer`` as a context manager to capture all output
(both LOGGER calls and data_to_stdout) and flush them atomically when the
block exits.
"""

from __future__ import annotations

import atexit
import logging
import logging.handlers
import queue
import re
import sys
import threading

# ── Module-level color control ────────────────────────────────────────────────

_NO_COLOR: bool = False

_ANSI_RE = re.compile(r"\x1b\[[\d;]*m")


def set_no_color(flag: bool) -> None:
    global _NO_COLOR
    _NO_COLOR = flag


def clear_colors(text: str) -> str:
    """Strip all ANSI escape codes from *text*."""
    return _ANSI_RE.sub("", text)


# ── Thread-local output buffering ─────────────────────────────────────────────

_tls = threading.local()
_flush_lock = threading.Lock()


def _is_buffering() -> bool:
    return getattr(_tls, "buffering", False)


def _buffer_line(line: str) -> None:
    """Append a fully-formatted line to the thread-local buffer."""
    buf: list[str] = getattr(_tls, "buffer", None) or []
    buf.append(line)
    _tls.buffer = buf


class OutputBuffer:
    """Context manager that buffers all thread output and flushes atomically.

    Usage::

        with OutputBuffer():
            LOGGER.info("line 1")
            data_to_stdout("block\\n")
            LOGGER.info("line 2")
        # all three lines are written to stdout together on __exit__
    """

    def __enter__(self) -> OutputBuffer:
        _tls.buffering = True
        _tls.buffer = []
        return self

    def __exit__(self, *exc: object) -> None:
        lines = getattr(_tls, "buffer", []) or []
        _tls.buffering = False
        _tls.buffer = []
        if not lines:
            return
        # Skip flush if an abort/interrupt occurred while buffering
        if exc[0] is KeyboardInterrupt:
            return
        chunk = "\n".join(lines) + "\n"
        with _flush_lock:
            sys.stdout.write(chunk)
            sys.stdout.flush()


# ── data_to_stdout — direct stdout writer ─────────────────────────────────────

_stdout_lock = threading.Lock()


def data_to_stdout(data: str, bold: bool = False) -> None:
    """Write directly to stdout, bypassing the logger.  Thread-safe."""
    if _NO_COLOR:
        data = clear_colors(data)
    elif bold:
        data = f"\033[1m{data}\033[0m"

    if _is_buffering():
        _buffer_line(data.rstrip("\n"))
        return

    with _stdout_lock:
        sys.stdout.write(data)
        sys.stdout.flush()


# ── Colorizing stream handler (modeled on sqlmap) ─────────────────────────────

# Phrases that trigger bold output for the entire line.
BOLD_PATTERNS = (
    "appears to be prompt-injectable",
    "does not appear to be",
    "not injectable",
    "prompt generation complete",
)

_LEVEL_COLORS: dict[str, str] = {
    "DEBUG":    "\033[94m",   # bright blue
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[1;31m", # bold red
}

_CYAN = "\033[36m"
_GREEN = "\033[32m"
_WHITE = "\033[97m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

_QUOTED_RE = re.compile(r"'([^']+)'")


def _colorize(message: str, level_name: str) -> str:
    """Apply sqlmap-style ANSI coloring to a formatted log line."""
    make_bold = any(p in message.lower() for p in BOLD_PATTERNS)

    message = re.sub(
        r"\[(\d{2}:\d{2}:\d{2})\]",
        rf"[{_CYAN}\1{_RESET}]",
        message,
        count=1,
    )

    level_color = _LEVEL_COLORS.get(level_name, "")
    if level_color:
        message = message.replace(
            f"[{level_name}]",
            f"[{level_color}{level_name}{_RESET}]",
            1,
        )

    message = _QUOTED_RE.sub(rf"'{_WHITE}\1{_RESET}'", message)

    if make_bold:
        message = f"{_BOLD}{message}{_RESET}"

    return message


class ColorizingStreamHandler(logging.StreamHandler):
    """StreamHandler that colorizes the formatted log line."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            message = _colorize(message, record.levelname)
            self.stream.write(message + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


# ── Buffering-aware handler ──────────────────────────────────────────────────
# Installed on the root logger alongside the QueueHandler.  When the calling
# thread is inside an OutputBuffer context, this handler formats + colorizes
# the record immediately in the calling thread and appends it to the
# thread-local buffer.  It returns True so the QueueHandler (which would
# dispatch to the listener thread) is skipped.

class _BufferingHandler(logging.Handler):
    """Intercept log records from buffered threads before they reach the queue."""

    def emit(self, record: logging.LogRecord) -> None:
        if not _is_buffering():
            return  # let the QueueHandler handle it
        try:
            message = self.format(record)
            if not _NO_COLOR:
                message = _colorize(message, record.levelname)
            _buffer_line(message)
        except Exception:
            self.handleError(record)


class _BufferingFilter(logging.Filter):
    """Attached to the QueueHandler — blocks records that were already captured
    by _BufferingHandler so they don't get written twice."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not _is_buffering()


# ── Formatter ─────────────────────────────────────────────────────────────────

_FORMATTER = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


# ── configure_logging ─────────────────────────────────────────────────────────

def configure_logging(verbose: bool, no_color: bool = False) -> None:
    set_no_color(no_color)
    level = logging.DEBUG if verbose else logging.INFO

    # The real handler that writes to stdout (runs in listener thread only)
    if no_color:
        stream_handler: logging.Handler = logging.StreamHandler(sys.stdout)
    else:
        stream_handler = ColorizingStreamHandler(sys.stdout)

    stream_handler.setFormatter(_FORMATTER)
    stream_handler.setLevel(level)

    # Queue handler: all threads write log records here (non-blocking)
    log_queue: queue.SimpleQueue[logging.LogRecord] = queue.SimpleQueue()
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.addFilter(_BufferingFilter())

    # Buffering handler: captures records from buffered threads directly
    buf_handler = _BufferingHandler()
    buf_handler.setFormatter(_FORMATTER)
    buf_handler.setLevel(level)

    # Listener: single dedicated thread reads from queue and calls stream_handler
    listener = logging.handlers.QueueListener(
        log_queue, stream_handler, respect_handler_level=True,
    )
    listener.start()
    atexit.register(listener.stop)

    # Reset existing handlers to prevent duplicates
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)

    root.addHandler(buf_handler)
    root.addHandler(queue_handler)
    root.setLevel(level)
