"""UI utilities for LLMMap — sqlmap-style output."""

from __future__ import annotations

import sys
import time
from typing import Any

BANNER = r"""
  _      _      __  __ __  __
 | |    | |    |  \/  |  \/  |
 | |    | |    | \  / | \  / | __ _ _ __
 | |    | |    | |\/| | |\/| |/ _` | '_ \
 | |____| |____| |  | | |  | | (_| | |_) |
 |______|______|_|  |_|_|  |_|\__,_| .__/
                                    | |
                                    |_|
"""

LEGAL_DISCLAIMER = (
    "Usage of LLMMap for attacking targets without prior mutual consent is "
    "illegal. It is the end user's responsibility to obey all applicable "
    "local, state and federal laws. Developers assume no liability and are "
    "not responsible for any misuse or damage caused by this program."
)

IDENTIFIED_HEADER = (
    "LLMMap identified the following injection point(s) with a total of "
    "{count} HTTP(s) requests"
)


def print_banner(version: str = "v1.0.0") -> None:
    """Print ASCII banner, version line, and legal disclaimer."""
    from llmmap.utils.logging import data_to_stdout

    data_to_stdout(f"\033[33m{BANNER}\033[0m")
    data_to_stdout(
        f"    \033[90m{version}\033[0m"
        f" | \033[94mhttps://github.com/Hellsender01/LLMMap\033[0m\n\n"
    )
    data_to_stdout(f"[!] legal disclaimer: {LEGAL_DISCLAIMER}\n\n")


def print_start_marker() -> None:
    """Print sqlmap-style ``[*] starting @`` marker."""
    from llmmap.utils.logging import data_to_stdout

    data_to_stdout(f"[*] starting @ {time.strftime('%H:%M:%S /%Y-%m-%d/')}\n\n")


def print_end_marker() -> None:
    """Print sqlmap-style ``[*] ending @`` marker."""
    from llmmap.utils.logging import data_to_stdout

    data_to_stdout(f"\n[*] ending @ {time.strftime('%H:%M:%S /%Y-%m-%d/')}\n\n")


def _resolve_param(finding: Any) -> tuple[str, str]:
    """Extract (param_name, place) from a finding's point_id."""
    parts = finding.point_id.split(":")
    if len(parts) >= 3 and parts[1] == "multipart":
        param_name = parts[2]
    elif len(parts) >= 3 and parts[1] == "json":
        param_name = ":".join(parts[2:])
    elif len(parts) >= 2:
        param_name = parts[1]
    else:
        param_name = finding.point_id

    place = "UNKNOWN"
    if "query:" in finding.point_id:
        place = "GET"
    elif "body:" in finding.point_id:
        place = "POST"
    elif "header:" in finding.point_id:
        place = "HEADER"
    elif "cookie:" in finding.point_id:
        place = "COOKIE"
    return param_name, place


def _format_prompt(text: str) -> str:
    """Collapse whitespace for display."""
    return " ".join(text.split())


def format_identification_block(
    header: str,
    findings: list,
    goal: str | None = None,
) -> str:
    """Format the sqlmap-style identification block for confirmed findings.

    sqlmap format: header + `---` + findings grouped by parameter + `---`
    """
    from llmmap.utils.logging import _NO_COLOR

    # Color codes (disabled if --no-color)
    G = "" if _NO_COLOR else "\033[32m"   # green
    W = "" if _NO_COLOR else "\033[97m"   # white/bright
    Y = "" if _NO_COLOR else "\033[33m"   # yellow
    C = "" if _NO_COLOR else "\033[36m"   # cyan
    B = "" if _NO_COLOR else "\033[1m"    # bold
    R = "" if _NO_COLOR else "\033[0m"    # reset

    # Group findings by parameter, preserving order
    seen: set[str] = set()
    grouped: dict[str, list] = {}
    group_order: list[str] = []

    for finding in findings:
        dedup_key = f"{finding.point_id}:{finding.rule_id}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        param_name, place = _resolve_param(finding)
        group_key = f"{param_name} ({place})"
        if group_key not in grouped:
            grouped[group_key] = []
            group_order.append(group_key)
        grouped[group_key].append(finding)

    lines = [f"{B}{header}{R}:\n---"]

    for group_key in group_order:
        lines.append(f"{B}Parameter: {G}{group_key}{R}")
        if goal:
            lines.append(f"    {Y}Goal:{R} {goal}")
        for finding in grouped[group_key]:
            lines.append(f"    {C}Type:{R} {finding.title}")
            if finding.prompt_text:
                p_line = _format_prompt(finding.prompt_text)
                lines.append(f"    {C}Prompt:{R} {W}{p_line}{R}")
            lines.append("")  # blank line between entries

    lines.append("---")
    return "\n".join(lines) + "\n"


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Standard [Y/n] interactive prompt."""
    from llmmap.utils.logging import _NO_COLOR

    suffix = " [Y/n]" if default else " [y/N]"
    prefix = "[?]" if _NO_COLOR else "\033[93m[?]\033[0m"
    try:
        user_input = input(f"{prefix} {prompt}{suffix}: ").strip().lower()
        if not user_input:
            return default
        return user_input in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        print("\n[!] User aborted.")
        sys.exit(1)
