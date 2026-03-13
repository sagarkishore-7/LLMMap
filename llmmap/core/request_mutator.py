"""Apply prompts to discovered injection points."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from llmmap.core.models import HttpRequest, InjectionPoint

_LOGGER = logging.getLogger(__name__)


def _inject_value(original: str, marker: str, prompt: str) -> str:
    if marker in original:
        return original.replace(marker, prompt)
    return prompt



def _replace_pair_values(
    pairs: list[tuple[str, str]],
    key: str,
    target_original: str,
    marker: str,
    prompt: str,
) -> list[tuple[str, str]]:
    replaced = False
    out: list[tuple[str, str]] = []
    for current_key, current_value in pairs:
        if (not replaced) and current_key == key and current_value == target_original:
            out.append((current_key, _inject_value(current_value, marker, prompt)))
            replaced = True
        else:
            out.append((current_key, current_value))
    if not replaced:
        out.append((key, prompt))
    return out



def apply_prompt(
    request: HttpRequest,
    point: InjectionPoint,
    prompt: str,
    marker: str,
) -> HttpRequest:
    """Create a new request by injecting prompt into the target point."""
    split = urlsplit(request.url)
    url = request.url
    # Remove Content-Length and Transfer-Encoding so HttpClient/urllib
    # recalculates them for the new body
    excluded = ("content-length", "transfer-encoding")
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in excluded
    }
    body = request.body

    if point.location == "query":
        pairs = parse_qsl(split.query, keep_blank_values=True)
        pairs = _replace_pair_values(pairs, point.key, point.original_value, marker, prompt)
        query = urlencode(pairs, doseq=True)
        url = urlunsplit((split.scheme, split.netloc, split.path, query, split.fragment))


    elif point.location == "body":
        content_type = request.headers.get("Content-Type", "").lower()
        if "multipart/form-data" in content_type:
            # Extract boundary from header (case-insensitive)
            boundary_match = re.search(
                r'boundary=([^;]+)',
                request.headers.get("Content-Type", ""),
                re.IGNORECASE,
            )
            if boundary_match:
                boundary = boundary_match.group(1).strip()
                # Remove quotes if present
                if boundary.startswith('"') and boundary.endswith('"'):
                    boundary = boundary[1:-1]
                
                # Split body by the actual boundary
                parts = body.split(f"--{boundary}")
                modified_parts = []
                injected = False
                
                for part in parts:
                    # Look for the target part by name and original value
                    if (
                        not injected
                        and f'name="{point.key}"' in part
                        and point.original_value in part
                    ):
                        # Split by double newline (handle both \r\n and \n)
                        val_match = re.search(r'(.*?\r?\n\r?\n)(.*)', part, re.DOTALL)
                        if val_match:
                            header_section = val_match.group(1)
                            value_section = val_match.group(2)
                            
                            # Preserve trailing newline before the next boundary
                            suffix = ""
                            if value_section.endswith("\r\n"):
                                suffix = "\r\n"
                                value_section = value_section[:-2]
                            elif value_section.endswith("\n"):
                                suffix = "\n"
                                value_section = value_section[:-1]
                            
                            new_val = _inject_value(value_section, marker, prompt)
                            modified_parts.append(header_section + new_val + suffix)
                            injected = True
                            continue
                    
                    modified_parts.append(part)
                
                if injected:
                    body = f"--{boundary}".join(modified_parts)
                    

        elif "application/json" in content_type:
            try:
                data = json.loads(request.body)
                
                # Reconstruct key path (e.g. messages[0].content -> ['messages', 0, 'content'])
                # point.key is "key_path" here because of our point_id format
                # We can inject at the precise location
                
                def apply_json_mutation(
                    obj: Any, path_str: str, orig_val: str, injected_val: str,
                ) -> bool:
                    # Simplistic path parser
                    # Split dots, extract brackets
                    parts = re.findall(r'[^.\[\]]+', path_str)

                    curr = obj
                    for _i, part in enumerate(parts[:-1]):
                        try:
                            if isinstance(curr, list):
                                curr = curr[int(part)]
                            else:
                                curr = curr[part]
                        except (KeyError, IndexError, ValueError) as exc:
                            _LOGGER.warning(
                                "JSON path traversal failed at %r in key=%s: %s",
                                part, path_str, exc,
                            )
                            return False

                    last_part = parts[-1]
                    try:
                        if isinstance(curr, list):
                            idx = int(last_part)
                            if curr[idx] == orig_val:
                                curr[idx] = injected_val
                                return True
                        else:
                            if curr.get(last_part) == orig_val:
                                curr[last_part] = injected_val
                                return True
                    except (KeyError, IndexError, ValueError) as exc:
                        _LOGGER.warning(
                            "JSON leaf mutation failed at %r in key=%s: %s",
                            last_part, path_str, exc,
                        )
                    return False

                new_val = _inject_value(point.original_value, marker, prompt)
                if apply_json_mutation(data, point.key, point.original_value, new_val):
                    body = json.dumps(data)
                else:
                    _LOGGER.warning(
                        "JSON body injection skipped for key=%s — path or value mismatch",
                        point.key,
                    )
            except (json.JSONDecodeError, TypeError) as exc:
                _LOGGER.warning(
                    "JSON body mutation failed for key=%s: %s", point.key, exc,
                )

        else:
            pairs = parse_qsl(body, keep_blank_values=True)
            pairs = _replace_pair_values(pairs, point.key, point.original_value, marker, prompt)
            body = urlencode(pairs, doseq=True)

    elif point.location == "header":
        if point.key in headers:
            headers[point.key] = _inject_value(headers[point.key], marker, prompt)
        else:
            headers[point.key] = prompt

    elif point.location == "cookie":
        cookie_header = headers.get("Cookie", "")
        cookie_pairs = []
        for chunk in cookie_header.split(";"):
            entry = chunk.strip()
            if not entry:
                continue
            if "=" in entry:
                key, value = entry.split("=", 1)
                cookie_pairs.append((key.strip(), value.strip()))
            else:
                cookie_pairs.append((entry, ""))

        cookie_pairs = _replace_pair_values(
            cookie_pairs,
            point.key,
            point.original_value,
            marker,
            prompt,
        )
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookie_pairs)

    elif point.location == "path":
        path = split.path or "/"
        replaced_path = _inject_value(path, marker, prompt)
        replaced_path = quote(replaced_path, safe="/=")
        url = urlunsplit((split.scheme, split.netloc, replaced_path, split.query, split.fragment))

    return HttpRequest(method=request.method, url=url, headers=headers, body=body)

