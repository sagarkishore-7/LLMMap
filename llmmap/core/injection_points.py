"""Injection point discovery for HTTP request components."""

from __future__ import annotations

import json
import re
from urllib.parse import parse_qsl, urlsplit

from llmmap.core.models import HttpRequest, InjectionPoint

_LOCATION_QUERY = "query"
_LOCATION_BODY = "body"
_LOCATION_HEADER = "header"
_LOCATION_COOKIE = "cookie"
_LOCATION_PATH = "path"



def _parse_cookie_pairs(cookie_header: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for chunk in cookie_header.split(";"):
        entry = chunk.strip()
        if not entry:
            continue
        if "=" in entry:
            key, value = entry.split("=", 1)
            out.append((key.strip(), value.strip()))
        else:
            out.append((entry, ""))
    return out



def _has_marker(request: HttpRequest, marker: str) -> bool:
    if marker in request.url or marker in request.body:
        return True
    return any(marker in key or marker in value for key, value in request.headers.items())



def discover_injection_points(
    request: HttpRequest,
    marker: str = "*",
    injection_points: str = "QBHCP",
    param_filter: tuple[str, ...] = (),
) -> list[InjectionPoint]:
    """Discover injection points using marker-first, fallback-to-all semantics."""
    points: list[InjectionPoint] = []
    has_marker = _has_marker(request, marker) if not param_filter else False
    selected = set(injection_points.upper())

    def include_all(flag: str) -> bool:
        return (not has_marker) and (flag in selected)

    parsed = urlsplit(request.url)

    if "Q" in selected:
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        for idx, (key, value) in enumerate(query_pairs):
            if marker in value or include_all("Q"):
                points.append(
                    InjectionPoint(
                        point_id=f"query:{key}:{idx}",
                        location=_LOCATION_QUERY,
                        key=key,
                        original_value=value,
                    )
                )



    if "B" in selected and request.body:
        content_type = request.headers.get("Content-Type", "").lower()
        if "multipart/form-data" in content_type:
            # Reconstruct boundary from header (case-insensitive for 'boundary=')
            boundary_match = re.search(
                r'boundary=([^;]+)',
                request.headers.get("Content-Type", ""),
                re.IGNORECASE,
            )
            if boundary_match:
                boundary = boundary_match.group(1).strip()
                if boundary.startswith('"') and boundary.endswith('"'):
                    boundary = boundary[1:-1]
                
                # Split body by boundary. body.split is usually fine
                # since the boundary itself won't change line endings.
                parts = request.body.split(f"--{boundary}")
                for idx, part in enumerate(parts):
                    # Each part starts with headers followed by double-newline and then the value.
                    # Handle both \r\n and \n for robustness.
                    if 'Content-Disposition' in part and 'name="' in part:
                        # Extract name
                        name_match = re.search(r'name="([^"]+)"', part)
                        key = name_match.group(1) if name_match else f"part_{idx}"
                        
                        # Extract value (between headers and the next boundary)
                        # Split by double newline (any combination of \r\n or \n)
                        val_match = re.search(r'(\r?\n\r?\n)(.*)', part, re.DOTALL)
                        if val_match:
                            value = val_match.group(2)
                            # Remove trailing newline before the next boundary
                            if value.endswith("\r\n"):
                                value = value[:-2]
                            elif value.endswith("\n"):
                                value = value[:-1]
                            
                            if marker in value or include_all("B"):
                                points.append(
                                    InjectionPoint(
                                        point_id=f"body:multipart:{key}:{idx}",
                                        location=_LOCATION_BODY,
                                        key=key,
                                        original_value=value,
                                    )
                                )

        elif "application/json" in content_type:
            try:
                data = json.loads(request.body)
                
                # We need to recursively traverse the JSON to find all leaf string values
                def extract_json_leaves(obj: object, prefix: str = "") -> list[tuple[str, str]]:
                    leaves = []
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            new_prefix = f"{prefix}.{k}" if prefix else k
                            leaves.extend(extract_json_leaves(v, new_prefix))
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj):
                            new_prefix = f"{prefix}[{i}]"
                            leaves.extend(extract_json_leaves(v, new_prefix))
                    elif isinstance(obj, str):
                        leaves.append((prefix, obj))
                    return leaves

                leaves = extract_json_leaves(data)
                for key_path, value in leaves:
                    if marker in value or include_all("B"):
                        points.append(
                            InjectionPoint(
                                point_id=f"body:json:{key_path}",
                                location=_LOCATION_BODY,
                                key=key_path,
                                original_value=value,
                            )
                        )
            except json.JSONDecodeError:
                pass # fall back or ignore malformed JSON

        else:
            body_pairs = parse_qsl(request.body, keep_blank_values=True)
            for idx, (key, value) in enumerate(body_pairs):
                if marker in value or include_all("B"):
                    points.append(
                        InjectionPoint(
                            point_id=f"body:{key}:{idx}",
                            location=_LOCATION_BODY,
                            key=key,
                            original_value=value,
                        )
                    )

    if "H" in selected:
        for key, value in request.headers.items():
            if key.lower() == "cookie":
                continue
            if marker in value or include_all("H"):
                points.append(
                    InjectionPoint(
                        point_id=f"header:{key}",
                        location=_LOCATION_HEADER,
                        key=key,
                        original_value=value,
                    )
                )

    if "C" in selected:
        cookie_header = request.headers.get("Cookie", "")
        for idx, (key, value) in enumerate(_parse_cookie_pairs(cookie_header)):
            if marker in value or include_all("C"):
                points.append(
                    InjectionPoint(
                        point_id=f"cookie:{key}:{idx}",
                        location=_LOCATION_COOKIE,
                        key=key,
                        original_value=value,
                    )
                )

    if "P" in selected:
        path = parsed.path or "/"
        if marker in path:
            for idx in range(path.count(marker)):
                points.append(
                    InjectionPoint(
                        point_id=f"path:marker:{idx}",
                        location=_LOCATION_PATH,
                        key="path",
                        original_value=path,
                    )
                )
        elif include_all("P"):
            points.append(
                InjectionPoint(
                    point_id="path:full",
                    location=_LOCATION_PATH,
                    key="path",
                    original_value=path,
                )
            )

    return points

