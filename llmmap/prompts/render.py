"""Prompt template renderer for placeholder substitution."""

from __future__ import annotations

import re

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")



def render_template(template: str, context: dict[str, str]) -> str:
    """Render template placeholders like {{KEY}} using provided context."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return context.get(key, match.group(0))

    return _PLACEHOLDER.sub(replace, template)
