"""Tests for the PromptLab simulation engine."""

from __future__ import annotations

import pytest

from promptlab.engine.simulator import run_simulation, list_techniques_for_scenario


def test_run_simulation_vulnerable_succeeds() -> None:
    result = run_simulation("support_bot", "rule_addition_prompting", "vulnerable")

    assert result.scenario_id == "support_bot"
    assert result.technique_id == "rule_addition_prompting"
    assert result.mode == "vulnerable"
    assert result.verdict.attack_succeeded is True
    assert result.verdict.confidence >= 0.8
    assert len(result.messages) == 3  # system, user, assistant
    assert result.messages[1].is_injection is True


def test_run_simulation_defended_fails() -> None:
    result = run_simulation("support_bot", "rule_addition_prompting", "defended")

    assert result.verdict.attack_succeeded is False
    assert result.mode == "defended"
    assert result.defense_description  # Should have defense info


def test_run_simulation_includes_technique_info() -> None:
    result = run_simulation("support_bot", "rule_addition_prompting", "vulnerable")

    assert result.technique_info is not None
    assert result.technique_info.family == "instruction_manipulation"
    assert result.technique_info.owasp_tag == "LLM01"
    assert result.technique_info.why_it_works
    assert result.technique_info.how_to_mitigate


def test_run_simulation_includes_system_prompt() -> None:
    result = run_simulation("support_bot", "rule_addition_prompting", "vulnerable")

    assert result.target_system_prompt
    assert "HelpBot" in result.target_system_prompt


def test_run_simulation_unknown_scenario_raises() -> None:
    with pytest.raises(ValueError, match="unknown scenario"):
        run_simulation("nonexistent", "some_technique", "vulnerable")


def test_run_simulation_invalid_mode_raises() -> None:
    with pytest.raises(ValueError):
        run_simulation("support_bot", "rule_addition_prompting", "invalid_mode")


def test_run_simulation_unknown_technique_still_works() -> None:
    """Unknown techniques should use the fallback generic injection."""
    result = run_simulation("support_bot", "totally_unknown_technique", "vulnerable")

    # The generic fallback injection should still trigger the vulnerable bot
    assert result.verdict.attack_succeeded is True


def test_list_techniques_returns_techniques() -> None:
    techniques = list_techniques_for_scenario("support_bot")

    assert len(techniques) > 0
    assert all("technique_id" in t for t in techniques)
    assert all("family" in t for t in techniques)
    families = {t["family"] for t in techniques}
    assert "instruction_manipulation" in families


def test_list_techniques_unknown_scenario() -> None:
    techniques = list_techniques_for_scenario("nonexistent")
    assert techniques == []


def test_to_dict_serialization() -> None:
    result = run_simulation("support_bot", "rule_addition_prompting", "vulnerable")
    data = result.to_dict()

    assert isinstance(data, dict)
    assert data["scenario_id"] == "support_bot"
    assert isinstance(data["messages"], list)
    assert isinstance(data["verdict"], dict)
    assert data["verdict"]["attack_succeeded"] is True
    assert isinstance(data["technique_info"], dict)


def test_multiple_techniques_work() -> None:
    """Verify several techniques work against the vulnerable target."""
    techniques = [
        "rule_addition_prompting",
        "rule_nullification_prompting",
        "instruction_ignoring_prompting",
        "instruction_forgetting_prompting",
    ]
    for tech_id in techniques:
        result = run_simulation("support_bot", tech_id, "vulnerable")
        assert result.verdict.attack_succeeded is True, (
            f"Expected {tech_id} to succeed in vulnerable mode"
        )


def test_multiple_techniques_blocked_in_defended() -> None:
    """Verify several techniques are blocked in defended mode."""
    techniques = [
        "rule_addition_prompting",
        "rule_nullification_prompting",
        "instruction_ignoring_prompting",
    ]
    for tech_id in techniques:
        result = run_simulation("support_bot", tech_id, "defended")
        assert result.verdict.attack_succeeded is False, (
            f"Expected {tech_id} to fail in defended mode"
        )
