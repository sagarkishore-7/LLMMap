from __future__ import annotations

from pathlib import Path

from llmmap.core.orchestrator import _apply_depth_profile
from llmmap.prompts.loader import load_prompts_from_dir


def test_depth_profile_limits_prompts_per_family() -> None:
    prompt_dir = Path(__file__).resolve().parent.parent / "llmmap" / "prompts" / "packs"
    prompts = load_prompts_from_dir(prompt_dir)
    limited = _apply_depth_profile(prompts, depth=1)
    counts: dict[str, int] = {}
    for prompt in limited:
        key = prompt.family.lower()
        counts[key] = counts.get(key, 0) + 1
    assert counts
    assert max(counts.values()) <= 1
