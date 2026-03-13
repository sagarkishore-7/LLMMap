"""Prompt selection filters."""

from __future__ import annotations

from llmmap.prompts.schema import PromptTechnique


def select_prompts(
    prompts: list[PromptTechnique],
    *,
    stage: str,
    families: tuple[str, ...],
    tags: tuple[str, ...],
    max_prompts: int,
) -> list[PromptTechnique]:
    """Select prompts by stage/family/tag."""
    family_set = {item.lower() for item in families if item}
    tag_set = {item.lower() for item in tags if item}

    selected: list[PromptTechnique] = []
    for prompt in prompts:
        if prompt.stage != stage:
            continue
        if family_set and prompt.family.lower() not in family_set:
            continue
        if tag_set and not tag_set.intersection({tag.lower() for tag in prompt.tags}):
            continue
        selected.append(prompt)

    if max_prompts > 0:
        return selected[:max_prompts]
    return selected
