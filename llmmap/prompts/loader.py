"""YAML prompt loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmmap.prompts.schema import PromptTechnique, PromptValidationError, validate_prompt


class PromptLoadError(ValueError):
    """Raised when prompt corpus cannot be loaded."""



def _tuple_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()



def _parse_prompt(raw: dict[str, Any], source: Path) -> PromptTechnique:
    technique = str(raw.get("technique", "")).strip()
    # Support both new 'prompt_id' and legacy 'payload_id' YAML keys
    prompt_id = raw.get("prompt_id") or raw.get("payload_id") or technique
    prompt = PromptTechnique(
        prompt_id=str(prompt_id).strip() if prompt_id else technique,
        family=str(raw.get("family", "")).strip(),
        technique=technique,
        template=str(raw.get("template", "")).strip(),
        requires=_tuple_str_list(raw.get("requires")),
        tags=_tuple_str_list(raw.get("tags")),
        stage=str(raw.get("stage", "stage1")).strip(),
        success_patterns=_tuple_str_list(raw.get("success_patterns")),
        suppress_patterns=_tuple_str_list(raw.get("suppress_patterns")),
        style_template=str(raw.get("style_template", "")).strip(),
    )

    try:
        validate_prompt(prompt)
    except PromptValidationError as exc:
        raise PromptLoadError(f"{source}: {exc}") from exc

    return prompt



def load_prompts_from_dir(prompt_dir: Path) -> list[PromptTechnique]:
    """Load and validate prompt definitions from YAML files in directory."""
    if not prompt_dir.exists() or not prompt_dir.is_dir():
        raise PromptLoadError(f"prompt directory does not exist: {prompt_dir}")

    prompts: list[PromptTechnique] = []
    seen_ids: set[str] = set()

    files = sorted(
        [
            path
            for path in prompt_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        ]
    )
    if not files:
        raise PromptLoadError(f"no YAML prompt files found in {prompt_dir}")

    for file_path in files:
        loaded = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        if loaded is None:
            continue
        if not isinstance(loaded, list):
            raise PromptLoadError(f"{file_path}: expected top-level list")

        for item in loaded:
            if not isinstance(item, dict):
                raise PromptLoadError(f"{file_path}: each prompt must be an object")
            prompt = _parse_prompt(item, file_path)
            if prompt.prompt_id in seen_ids:
                raise PromptLoadError(f"duplicate technique name: {prompt.prompt_id}")
            seen_ids.add(prompt.prompt_id)
            prompts.append(prompt)

    return prompts
