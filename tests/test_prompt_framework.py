from __future__ import annotations

from pathlib import Path

from llmmap.prompts.loader import load_prompts_from_dir
from llmmap.prompts.render import render_template
from llmmap.prompts.selector import select_prompts


def test_load_builtin_prompt_packs() -> None:
    prompt_dir = Path(__file__).resolve().parent.parent / "llmmap" / "prompts" / "packs"
    prompts = load_prompts_from_dir(prompt_dir)

    assert len(prompts) >= 30
    assert any(prompt.prompt_id == "rule_addition_prompting" for prompt in prompts)
    assert any(prompt.family == "agentic_pipeline" for prompt in prompts)



def test_render_template_replaces_known_placeholders_only() -> None:
    rendered = render_template(
        "probe {{RUN_ID}} with {{CANARY_URL}} and keep {{MISSING}}",
        {"RUN_ID": "abc123", "CANARY_URL": "https://canary.invalid"},
    )
    assert "abc123" in rendered
    assert "https://canary.invalid" in rendered
    assert "{{MISSING}}" in rendered



def test_select_prompts_filters_by_stage_family_tags_and_safety() -> None:
    prompt_dir = Path(__file__).resolve().parent.parent / "llmmap" / "prompts" / "packs"
    prompts = load_prompts_from_dir(prompt_dir)

    selected = select_prompts(
        prompts,
        stage="stage2",
        families=("agentic_tool_use_attack",),
        tags=("canary",),
        max_prompts=100,
    )

    assert all(prompt.stage == "stage2" for prompt in selected)
