"""Tests for the PromptLab FastAPI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from promptlab.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "promptlab"


def test_list_scenarios() -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 1
    assert scenarios[0]["scenario_id"] == "support_bot"


def test_get_scenario_detail() -> None:
    response = client.get("/api/scenarios/support_bot")
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "support_bot"
    assert data["title"]
    assert data["goal"]


def test_get_scenario_not_found() -> None:
    response = client.get("/api/scenarios/nonexistent")
    assert response.status_code == 404


def test_get_techniques() -> None:
    response = client.get("/api/scenarios/support_bot/techniques")
    assert response.status_code == 200
    techniques = response.json()
    assert len(techniques) > 0
    assert all("technique_id" in t for t in techniques)


def test_simulate_vulnerable() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "support_bot",
        "technique_id": "rule_addition_prompting",
        "mode": "vulnerable",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"]["attack_succeeded"] is True
    assert len(data["messages"]) == 3
    assert data["technique_info"] is not None
    assert data["target_system_prompt"]
    assert data["simulation_mode"] == "deterministic"


def test_simulate_defended() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "support_bot",
        "technique_id": "rule_addition_prompting",
        "mode": "defended",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"]["attack_succeeded"] is False
    assert data["defense_description"]


def test_simulate_unknown_scenario() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "nonexistent",
        "technique_id": "rule_addition_prompting",
        "mode": "vulnerable",
    })
    assert response.status_code == 404


def test_simulate_invalid_mode() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "support_bot",
        "technique_id": "rule_addition_prompting",
        "mode": "invalid",
    })
    assert response.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# Knowledge Assistant scenario
# ---------------------------------------------------------------------------


def test_list_scenarios_includes_knowledge() -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    ids = [s["scenario_id"] for s in response.json()]
    assert "support_bot" in ids
    assert "knowledge_assistant" in ids


def test_knowledge_techniques_endpoint() -> None:
    response = client.get("/api/scenarios/knowledge_assistant/techniques")
    assert response.status_code == 200
    techniques = response.json()
    assert len(techniques) > 0
    families = {t["family"] for t in techniques}
    assert "indirect_prompt_injection_context_data" in families


def test_simulate_knowledge_vulnerable() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "knowledge_assistant",
        "technique_id": "compromised_external_source_injection",
        "mode": "vulnerable",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"]["attack_succeeded"] is True
    assert data["target_system_prompt"]


def test_simulate_knowledge_defended() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "knowledge_assistant",
        "technique_id": "compromised_external_source_injection",
        "mode": "defended",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"]["attack_succeeded"] is False
    assert data["defense_description"]


# ---------------------------------------------------------------------------
# Memory Bot scenario
# ---------------------------------------------------------------------------


def test_list_scenarios_includes_memory_bot() -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    ids = [s["scenario_id"] for s in response.json()]
    assert "memory_bot" in ids


def test_memory_bot_techniques_endpoint() -> None:
    response = client.get("/api/scenarios/memory_bot/techniques")
    assert response.status_code == 200
    techniques = response.json()
    assert len(techniques) > 0
    families = {t["family"] for t in techniques}
    assert "cognitive_control_bypass" in families


def test_simulate_memory_bot_vulnerable() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "memory_bot",
        "technique_id": "context_poisoning",
        "mode": "vulnerable",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"]["attack_succeeded"] is True
    # Multi-turn: should have more than 3 messages
    assert len(data["messages"]) >= 7
    assert data["target_system_prompt"]


# ---------------------------------------------------------------------------
# /api/techniques endpoint
# ---------------------------------------------------------------------------


def test_get_all_techniques() -> None:
    response = client.get("/api/techniques")
    assert response.status_code == 200
    techniques = response.json()
    assert len(techniques) == 227
    assert all("technique_id" in t for t in techniques)
    assert all("family" in t for t in techniques)
    assert all("tags" in t for t in techniques)
    assert all("has_explanation" in t for t in techniques)
    assert all("scenarios" in t for t in techniques)


def test_get_techniques_filter_by_family() -> None:
    response = client.get("/api/techniques?family=instruction_manipulation")
    assert response.status_code == 200
    techniques = response.json()
    assert len(techniques) > 0
    assert all(t["family"] == "instruction_manipulation" for t in techniques)


def test_get_techniques_filter_unknown_family() -> None:
    response = client.get("/api/techniques?family=nonexistent_family")
    assert response.status_code == 200
    assert response.json() == []


def test_techniques_include_scenario_mapping() -> None:
    response = client.get("/api/techniques?family=instruction_manipulation")
    assert response.status_code == 200
    techniques = response.json()
    # instruction_manipulation is used by support_bot
    for t in techniques:
        assert "support_bot" in t["scenarios"]


def test_techniques_has_explanation_flag() -> None:
    response = client.get("/api/techniques")
    assert response.status_code == 200
    techniques = response.json()
    explained = [t for t in techniques if t["has_explanation"]]
    unexplained = [t for t in techniques if not t["has_explanation"]]
    assert len(explained) > 0
    assert len(unexplained) > 0


def test_simulate_memory_bot_defended() -> None:
    response = client.post("/api/simulate", json={
        "scenario_id": "memory_bot",
        "technique_id": "context_poisoning",
        "mode": "defended",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"]["attack_succeeded"] is False
    assert data["defense_description"]
    # Multi-turn: should have more than 3 messages
    assert len(data["messages"]) >= 7
