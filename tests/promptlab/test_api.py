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
