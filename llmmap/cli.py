"""CLI entrypoint for LLMMap."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from llmmap.config import RuntimeConfig
from llmmap.core.run import create_run_workspace
from llmmap.core.scanner import run_scan
from llmmap.core.ui import print_banner, print_end_marker, print_start_marker
from llmmap.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def _parse_params(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        for part in raw.split(","):
            name = part.strip()
            if not name:
                continue
            lowered = name.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            out.append(name)
    return out


def _list_families(prompt_dir: Path | None) -> None:
    """Print available prompt families and exit."""
    from llmmap.prompts.loader import load_prompts_from_dir

    packs_dir = prompt_dir or Path(__file__).parent / "prompts" / "packs"
    prompts = load_prompts_from_dir(packs_dir)

    families: dict[str, int] = {}
    for p in prompts:
        families[p.family] = families.get(p.family, 0) + 1

    print("available prompt families:\n")
    for family, count in sorted(families.items()):
        print(f"  {family} ({count} techniques)")
    print(f"\ntotal: {len(prompts)} techniques across {len(families)} families")


def _apply_sqlmap_style_mappings(args: argparse.Namespace) -> None:
    pass



def _build_examples() -> str:
    """Build the examples epilog with ANSI colors when stdout is a TTY."""
    import sys as _sys

    use_color = (
        _sys.stdout.isatty()
        and "--no-color" not in _sys.argv
        and "--disable-coloring" not in _sys.argv
    )

    G = "\033[32m" if use_color else ""   # green (commands)
    C = "\033[36m" if use_color else ""   # cyan (comments)
    W = "\033[97m" if use_color else ""   # white (quoted strings)
    B = "\033[1m" if use_color else ""    # bold (header)
    R = "\033[0m" if use_color else ""    # reset

    examples = [
        (
            "URL target with injection marker (local Ollama, no API key needed)",
            f'{G}llmmap{R} {G}-u{R} '
            f'{W}"https://target.example.com/chat?q=*"{R} '
            f'{G}--goal{R} {W}"reveal the system prompt"{R}',
        ),
        (
            "Burp Suite request capture",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"reveal the hidden password"{R}',
        ),
        (
            "OpenAI GPT as generator/judge backend",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"leak user data"{R} '
            f'{G}--provider{R} {W}openai{R} {G}--model{R} {W}gpt-4o{R}',
        ),
        (
            "Anthropic Claude backend",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"bypass content filter"{R} '
            f'{G}--provider{R} {W}anthropic{R}',
        ),
        (
            "Higher intensity scan (more prompts per family, obfuscation enabled)",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"extract API keys"{R} '
            f'{G}--intensity{R} {W}3{R}',
        ),
        (
            "Outbound callback detection with Burp Collaborator",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"trigger SSRF"{R} '
            f'{G}--callback-url{R} '
            f'{W}"https://xyz.burpcollaborator.net"{R}',
        ),
        (
            "Limit to specific parameters and injection point classes",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"reveal secrets"{R} '
            f'{G}-p{R} {W}prompt{R} {G}-p{R} {W}user{R} '
            f'{G}--injection-points{R} {W}QB{R}',
        ),
        (
            "Custom prompt families only",
            f'{G}llmmap{R} {G}-r{R} {W}request.xml{R} '
            f'{G}--goal{R} {W}"exfiltrate data"{R} '
            f'{G}--prompt-family{R} {W}jailbreak{R} '
            f'{G}--prompt-family{R} {W}role_play{R}',
        ),
    ]

    lines = [f"{B}examples:{R}"]
    for comment, cmd in examples:
        lines.append(f"  {C}# {comment}{R}")
        lines.append(f"  {cmd}")
        lines.append("")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLMMap - automated LLM security testing",
        epilog=_build_examples(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Target ────────────────────────────────────────────────────────
    target_group = parser.add_argument_group("Target")
    target_group.add_argument("-u", "--target-url", default=None, help="target URL")
    target_group.add_argument(
        "-r", "--request-file", type=Path, default=None, help="Burp Suite request file"
    )
    target_group.add_argument(
        "--goal", default="",
        metavar="GOAL",
        help="attacker objective (e.g. \"reveal the hidden password\")"
    )

    # ── Scan ──────────────────────────────────────────────────────────
    scan_group = parser.add_argument_group("Scan")
    scan_group.add_argument(
        "-p", "--param", action="append", dest="params", default=[],
        help="parameter(s) to test, e.g. -p q or -p q,user"
    )
    scan_group.add_argument(
        "--intensity", type=int, default=1,
        help="scan intensity 1-5 (default: 1)"
    )
    scan_group.add_argument(
        "--mode",
        choices=("dry", "live"),
        default="live",
        help="scan mode (default: live)",
    )
    scan_group.add_argument("--threads", type=int, default=1, help="concurrent HTTP requests")
    scan_group.add_argument(
        "--tap",
        action="store_true",
        help="enable TAP (Tree of Attacks with Pruning) iterative prompt refinement",
    )
    scan_group.add_argument(
        "--tap-depth", type=int, default=None,
        help="TAP search tree depth (default: 3)",
    )
    scan_group.add_argument(
        "--tap-width", type=int, default=None,
        help="TAP frontier width per depth level (default: 2)",
    )
    scan_group.add_argument(
        "--tap-budget", type=int, default=None,
        help="max HTTP queries for TAP stage (default: 18)",
    )

    # ── Request ───────────────────────────────────────────────────────
    request_group = parser.add_argument_group("Request")
    request_group.add_argument("--method", default=None, help="HTTP method override")
    request_group.add_argument(
        "--header",
        action="append",
        dest="headers",
        default=[],
        help="add header (e.g. --header \"X-Custom: val\")",
    )
    request_group.add_argument(
        "--cookie",
        action="append",
        dest="cookies",
        default=[],
        help="add cookie (e.g. --cookie \"session=abc\")",
    )
    request_group.add_argument("--data", default=None, help="request body")
    request_group.add_argument(
        "--proxy",
        default=None,
        help="HTTP(S) proxy URL (e.g. http://127.0.0.1:8080)",
    )
    request_group.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds (default: 10)",
    )
    request_group.add_argument(
        "--retries",
        type=int,
        default=1,
        help="HTTP retry attempts (default: 1)",
    )
    request_group.add_argument(
        "--verify-ssl",
        action="store_true",
        help="verify TLS certificates",
    )
    request_group.add_argument(
        "--scheme",
        choices=("http", "https"),
        default="https",
        help="scheme fallback (default: https)",
    )
    request_group.add_argument("--marker", default="*", help="injection point marker (default: *)")
    request_group.add_argument(
        "--injection-points",
        default="QBHCP",
        help="vectors to test: Q(query),B(body),H(header),C(cookie),P(path)",
    )
    request_group.add_argument(
        "--ignore-code",
        default="",
        help="ignore HTTP status codes (e.g. 401,403)",
    )

    # ── Prompts ───────────────────────────────────────────────────────
    prompt_group = parser.add_argument_group("Prompts")
    prompt_group.add_argument(
        "--prompt-dir",
        type=Path,
        default=None,
        help="custom prompt pack directory",
    )
    prompt_group.add_argument(
        "--prompt-family",
        action="append",
        dest="prompt_families",
        default=[],
        nargs="?",
        const="__list__",
        help="filter by family (no value to list families)",
    )
    prompt_group.add_argument(
        "--prompt-tag",
        action="append",
        dest="prompt_tags",
        default=[],
        help="filter by tag (e.g. llm01)",
    )
    prompt_group.add_argument(
        "--max-prompts",
        type=int,
        default=0,
        help="max prompts after filtering (0=auto, scales with intensity)",
    )
    prompt_group.add_argument(
        "--callback-url", default=None, metavar="URL",
        help="listener URL for outbound callback prompts"
    )

    # ── Detection ─────────────────────────────────────────────────────
    detect_group = parser.add_argument_group("Detection")
    detect_group.add_argument(
        "--detector-threshold",
        type=float,
        default=0.6,
        help="score threshold for positive signal (default: 0.6)",
    )
    detect_group.add_argument(
        "--match-regex",
        action="append",
        dest="match_regex",
        default=[],
        help="custom regex to match in responses",
    )
    detect_group.add_argument(
        "--match-keyword",
        action="append",
        dest="match_keywords",
        default=[],
        help="custom keyword to match in responses",
    )
    detect_group.add_argument(
        "--no-fp-suppression",
        action="store_true",
        help="disable false-positive suppression",
    )
    detect_group.add_argument(
        "--reliability-retries",
        type=int,
        default=5,
        help="confirmation retries per candidate (default: 5)",
    )
    detect_group.add_argument(
        "--confirm-threshold",
        type=int,
        default=3,
        help="successes required to confirm (default: 3)",
    )

    # ── LLM Provider ────────────────────────────────────────────────────
    provider_group = parser.add_argument_group("LLM Provider")
    provider_group.add_argument(
        "--provider",
        choices=("ollama", "openai", "anthropic", "google"),
        default="ollama",
        help="LLM backend (default: ollama)",
    )
    provider_group.add_argument(
        "--model",
        default=None,
        help="model name (default depends on provider)",
    )
    provider_group.add_argument(
        "--api-key",
        default=None,
        help="API key (or set OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY)",
    )
    provider_group.add_argument(
        "--base-url",
        default=None,
        help="base URL for OpenAI-compatible servers",
    )

    # ── Output ────────────────────────────────────────────────────────
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs"),
        dest="output_dir",
        help="scan results directory (default: runs/)",
    )
    output_group.add_argument(
        "--report-format",
        action="append",
        dest="report_formats",
        default=[],
        help=(
            "report output format: json, markdown, sarif, all "
            "(default: all). Can be specified multiple times"
        ),
    )
    output_group.add_argument(
        "--purge-old-runs",
        action="store_true",
        help="delete previous scan folders",
    )
    output_group.add_argument(
        "--no-color", "--disable-coloring",
        action="store_true",
        dest="no_color",
        help="disable console coloring",
    )
    output_group.add_argument("--verbose", action="store_true", help="enable debug logging")

    return parser



def app(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _apply_sqlmap_style_mappings(args)

    # --prompt-family with no value: list available families and exit
    if "__list__" in args.prompt_families:
        _list_families(args.prompt_dir)
        return 0

    configure_logging(verbose=args.verbose, no_color=args.no_color)
    print_banner()
    print_start_marker()

    stages: tuple[str, ...] = ("stage1",)
    if args.tap:
        stages = ("stage1", "stage3_tap")
    if args.intensity < 1 or args.intensity > 5:
        LOGGER.error("--intensity must be between 1 and 5")
        return 2

    # ── Resolve LLM provider config ─────────────────────────────────────────
    import os as _os

    _PROVIDER_DEFAULT_MODELS = {
        "ollama": _os.environ.get("OLLAMA_MODEL", "qwen3-coder-next:cloud"),
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
        "google": "gemini-2.0-flash",
    }
    _PROVIDER_ENV_KEYS = {
        "ollama": "OLLAMA_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    resolved_model = args.model or _PROVIDER_DEFAULT_MODELS.get(args.provider, "qwen3-coder-next:cloud")

    # API key: CLI flag -> environment variable
    resolved_api_key = args.api_key
    if resolved_api_key is None:
        env_var = _PROVIDER_ENV_KEYS.get(args.provider)
        if env_var:
            resolved_api_key = _os.environ.get(env_var)

    # Cloud providers (including Ollama Cloud) require an API key.
    # Local Ollama (OLLAMA_BASE_URL=http://127.0.0.1:11434) works without one.
    if args.provider in ("openai", "anthropic", "google") and not resolved_api_key:
        env_var = _PROVIDER_ENV_KEYS.get(args.provider, "")
        LOGGER.error(
            "--api-key is required for provider %r (or set %s env var)",
            args.provider, env_var,
        )
        print_end_marker()
        return 2

    # Headers are parsed here to allow for custom logic
    # (e.g. stripping whitespace, validating format)
    _headers = tuple(
        line.strip() for line in args.headers if line.strip() and ":" in line
    )
    
    ignore_code: tuple[int, ...] = ()
    if args.ignore_code:
        ignore_code = tuple(
            int(x.strip())
            for x in args.ignore_code.split(",")
            if x.strip() and x.strip().isdigit()
        )

    # ── Resolve report formats ──────────────────────────────────────────
    _VALID_REPORT_FORMATS = {"json", "markdown", "sarif"}
    if args.report_formats:
        resolved_formats: set[str] = set()
        for fmt in args.report_formats:
            for part in fmt.split(","):
                part = part.strip().lower()
                if part == "all":
                    resolved_formats = set(_VALID_REPORT_FORMATS)
                    break
                if part in _VALID_REPORT_FORMATS:
                    resolved_formats.add(part)
                else:
                    LOGGER.warning("unknown report format %r (valid: json, markdown, sarif, all)", part)
        report_formats = tuple(sorted(resolved_formats))
    else:
        report_formats = ("json", "markdown", "sarif")

    config = RuntimeConfig(
        mode=args.mode,
        enabled_stages=stages,
        target_url=args.target_url,
        run_root=args.output_dir,
        request_file=args.request_file,
        method=args.method,
        param_filter=tuple(_parse_params(args.params)),
        headers=tuple(args.headers),
        cookies=tuple(args.cookies),
        data=args.data,
        marker=args.marker,
        injection_points=args.injection_points,
        scheme=args.scheme,
        timeout_seconds=args.timeout,
        retries=args.retries,
        proxy=args.proxy,
        verify_ssl=args.verify_ssl,
        prompt_dir=args.prompt_dir,
        prompt_stage="stage1",
        prompt_families=tuple(args.prompt_families),
        prompt_tags=tuple(args.prompt_tags),
        max_prompts=args.max_prompts,
        detector_threshold=args.detector_threshold,
        fp_suppression=not args.no_fp_suppression,
        reliability_retries=args.reliability_retries,
        confirm_threshold=args.confirm_threshold,
        intensity=args.intensity,
        match_regex=tuple(args.match_regex),
        match_keywords=tuple(args.match_keywords),
        secret_hints=(),
        temperature_sweep=(),
        repro_check=False,
        oob_provider="none",  # OOB: stage 2+ only — not available in this release
        interactsh_client_path="interactsh-client",
        interactsh_server=None,
        interactsh_token=None,
        canary_domain=None,
        oob_wait_seconds=10.0,
        oob_poll_interval=5,
        mutation_profile="baseline",
        mutation_max_variants=6,
        context_feedback=False,
        pivot_attacks=False,
        interactive=False,
        local_generator=None,
        canary_listener=False,
        canary_listener_host="127.0.0.1",
        canary_listener_port=8787,
        threads=args.threads,
        # TAP (stage 3)
        tap_goal=args.goal,
        tap_depth=args.tap_depth if args.tap_depth is not None else 3,
        tap_width=args.tap_width if args.tap_width is not None else 2,
        tap_query_budget=args.tap_budget if args.tap_budget is not None else 18,
        semantic_use_provider=False,
        operator_id="unknown",
        retention_days=0,
        purge_old_runs=args.purge_old_runs,
        ignore_code=ignore_code,
        goal=args.goal,
        llm_provider=args.provider,
        llm_model=resolved_model,
        llm_api_key=resolved_api_key,
        llm_base_url=args.base_url or _os.environ.get("OLLAMA_BASE_URL") if args.provider == "ollama" else args.base_url,
        callback_url=args.callback_url,
        data_flow=False,
        report_formats=report_formats,
    )

    # --goal is required for the LLM-driven generation pipeline
    if not config.goal:
        LOGGER.error(
            "--goal is required (e.g. --goal \"reveal the hidden password\"). "
            "Specify the attacker objective so LLMMap can generate targeted prompts."
        )
        print_end_marker()
        return 2

    try:
        run_dir = create_run_workspace(config)
        _report = run_scan(config, run_dir)
    except ValueError as exc:
        LOGGER.error(str(exc))
        print_end_marker()
        return 2

    print_end_marker()
    return 0



def main() -> None:
    raise SystemExit(app())


if __name__ == "__main__":
    main()
