"""PromptLab FastAPI application.

Endpoints:
    GET  /api/health                    -- Health check
    GET  /api/scenarios                 -- List available scenarios
    GET  /api/scenarios/{id}            -- Get scenario details
    GET  /api/scenarios/{id}/techniques -- List techniques for a scenario
    GET  /api/techniques                -- List all techniques in the catalog
    POST /api/simulate                  -- Run a simulation

Deployment:
    Railway sets PORT automatically.  Run with::

        uvicorn promptlab.api.main:app --host 0.0.0.0 --port $PORT

    Or use the ``if __name__`` block at the bottom for a quick start.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from promptlab.engine.simulator import list_all_techniques, list_techniques_for_scenario, run_simulation
from promptlab.scenarios.registry import get_scenario, list_scenarios

LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="PromptLab",
    description="Interactive AI security lab -- learn prompt injection through safe sandbox scenarios.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS -- defaults to the local Next.js dev server; override with
# PROMPTLAB_CORS_ORIGINS (comma-separated) for production.
# ---------------------------------------------------------------------------

_DEFAULT_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
_cors_env = os.environ.get("PROMPTLAB_CORS_ORIGINS")
_allowed_origins = [o.strip() for o in _cors_env.split(",")] if _cors_env else _DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SimulateRequest(BaseModel):
    scenario_id: str = Field(..., description="Scenario to run")
    technique_id: str = Field(..., description="Attack technique to use")
    mode: str = Field(
        ...,
        pattern="^(vulnerable|defended)$",
        description="Target mode: 'vulnerable' or 'defended'",
    )


class MessageResponse(BaseModel):
    role: str
    content: str
    is_injection: bool = False


class VerdictResponse(BaseModel):
    attack_succeeded: bool
    confidence: float
    reasoning: str
    method: str


class TechniqueInfoResponse(BaseModel):
    technique_id: str
    family: str
    name: str
    description: str
    owasp_tag: str
    why_it_works: str
    how_to_mitigate: str


class SimulateResponse(BaseModel):
    scenario_id: str
    technique_id: str
    mode: str
    messages: list[MessageResponse]
    verdict: VerdictResponse
    technique_info: TechniqueInfoResponse | None = None
    target_system_prompt: str
    defense_description: str
    simulation_mode: str = "deterministic"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "promptlab"}


@app.get("/api/scenarios")
def get_scenarios() -> list[dict[str, Any]]:
    return list_scenarios()


@app.get("/api/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str) -> dict[str, Any]:
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return scenario.to_dict()


@app.get("/api/scenarios/{scenario_id}/techniques")
def get_techniques(scenario_id: str) -> list[dict[str, Any]]:
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return list_techniques_for_scenario(scenario_id)


@app.get("/api/techniques")
def get_all_techniques(family: str | None = None) -> list[dict[str, Any]]:
    """Return the full technique catalog from the LLMMap prompt packs.

    Optional query parameter ``family`` filters by attack family.
    """
    techniques = list_all_techniques()
    if family:
        techniques = [t for t in techniques if t["family"] == family]
    return techniques


@app.post("/api/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest) -> dict[str, Any]:
    """Run a simulation and return the full result.

    This endpoint targets ONLY built-in sandbox scenarios.
    It does NOT accept arbitrary URLs or external targets.
    """
    scenario = get_scenario(request.scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{request.scenario_id}' not found",
        )

    try:
        result = run_simulation(
            scenario_id=request.scenario_id,
            technique_id=request.technique_id,
            mode=request.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result.to_dict()


# ---------------------------------------------------------------------------
# Entrypoint for Railway / direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
