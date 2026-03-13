"""Prompt schema and validation."""

from __future__ import annotations

from dataclasses import dataclass


class PromptValidationError(ValueError):
    """Raised when prompt definition is invalid."""


@dataclass(frozen=True)
class PromptTechnique:
    prompt_id: str
    family: str
    technique: str
    template: str
    requires: tuple[str, ...]
    tags: tuple[str, ...]
    stage: str
    success_patterns: tuple[str, ...] = ()
    suppress_patterns: tuple[str, ...] = ()
    # Framing/structure for LLM-driven goal injection (uses {{GOAL_PROMPT}})
    style_template: str = ""



def validate_prompt(prompt: PromptTechnique) -> None:
    if not prompt.prompt_id:
        raise PromptValidationError("prompt.id is required")
    if not prompt.family:
        raise PromptValidationError(f"prompt {prompt.prompt_id}: family is required")
    if not prompt.technique:
        raise PromptValidationError(f"prompt {prompt.prompt_id}: technique is required")
    if not prompt.template:
        raise PromptValidationError(f"prompt {prompt.prompt_id}: template is required")
    if not prompt.stage:
        raise PromptValidationError(f"prompt {prompt.prompt_id}: stage is required")
