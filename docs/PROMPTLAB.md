# PromptLab — Interactive AI Security Lab

PromptLab is an interactive web-based lab built on top of LLMMap for learning and demonstrating prompt injection techniques through safe sandbox scenarios.

## Quick Start

### 1. Start the backend

```bash
# From the project root
source .venv/bin/activate
uvicorn promptlab.api.main:app --reload --port 8000
```

### 2. Start the frontend

```bash
cd web
npm run dev
```

### 3. Open the lab

Navigate to [http://localhost:3000](http://localhost:3000).

## How It Works

1. **Select a scenario** — each scenario is a sandboxed vulnerable application (e.g., a support chatbot with a hidden system prompt).
2. **Choose an attack technique** — pick from the LLMMap technique library (e.g., rule addition, instruction forgetting).
3. **Run the simulation** — the engine fires the attack against the sandbox target and judges the result.
4. **Toggle vulnerable/defended** — see the same attack against both an unprotected and a hardened version.
5. **Learn from the explanation panel** — understand what the technique is, why it works, and how to defend against it.

## Architecture

```
┌─────────────────┐     HTTP/JSON     ┌──────────────────┐
│   Next.js UI    │ ◄──────────────► │   FastAPI API    │
│   (web/)        │                   │   (promptlab/    │
│                 │                   │    api/)         │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                    ┌──────────┴─────────┐
                                    │  Simulation Engine  │
                                    │  (promptlab/        │
                                    │   engine/)          │
                                    └──────────┬─────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                     ┌────────┴──────┐  ┌──────┴──────┐  ┌─────┴──────┐
                     │   Sandbox     │  │   LLMMap    │  │   Judge    │
                     │   Targets     │  │   Prompts   │  │            │
                     │  (scenarios/) │  │   (llmmap/  │  │            │
                     └───────────────┘  │   prompts/) │  └────────────┘
                                        └─────────────┘
```

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| **Scenario Registry** | `promptlab/scenarios/registry.py` | Defines available lab scenarios with metadata |
| **Sandbox Targets** | `promptlab/scenarios/targets.py` | Vulnerable and defended target implementations |
| **Simulation Engine** | `promptlab/engine/simulator.py` | Runs attack → target → judge pipeline |
| **Schemas** | `promptlab/engine/schemas.py` | Shared data models (SimulationResult, Verdict, etc.) |
| **FastAPI App** | `promptlab/api/main.py` | REST API endpoints |
| **Frontend** | `web/app/page.tsx` | React UI with chat visualization |

### Reused from LLMMap

- **227 attack techniques** from the YAML prompt packs
- **Template rendering** (`llmmap/prompts/render.py`)
- **Technique selection** (`llmmap/prompts/selector.py`)
- **Prompt loading** (`llmmap/prompts/loader.py`)

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/scenarios` | List all scenarios |
| GET | `/api/scenarios/{id}` | Get scenario details |
| GET | `/api/scenarios/{id}/techniques` | List techniques for a scenario |
| POST | `/api/simulate` | Run a simulation |

### POST /api/simulate

Request:
```json
{
  "scenario_id": "support_bot",
  "technique_id": "rule_addition_prompting",
  "mode": "vulnerable"
}
```

Response:
```json
{
  "scenario_id": "support_bot",
  "technique_id": "rule_addition_prompting",
  "mode": "vulnerable",
  "messages": [
    {"role": "system", "content": "[System prompt hidden]", "is_injection": false},
    {"role": "user", "content": "...", "is_injection": true},
    {"role": "assistant", "content": "..."}
  ],
  "verdict": {
    "attack_succeeded": true,
    "confidence": 1.0,
    "reasoning": "The target response contains the secret value 'AURORA-7X-CLASSIFIED'.",
    "method": "deterministic"
  },
  "technique_info": {
    "name": "Rule Addition",
    "family": "instruction_manipulation",
    "owasp_tag": "LLM01",
    "why_it_works": "...",
    "how_to_mitigate": "..."
  },
  "target_system_prompt": "...",
  "defense_description": ""
}
```

## Available Scenarios

### Support Bot: Hidden System Prompt (Beginner)

A customer support chatbot with a confidential admin password hidden in its system prompt. The attacker's goal is to extract the password using direct prompt injection.

- **Vulnerable mode:** No input filtering, weak system prompt boundaries
- **Defended mode:** Input filtering + hardened system prompt with instruction hierarchy
- **Attack family:** instruction_manipulation (22 techniques)
- **OWASP mapping:** LLM01 — Prompt Injection

### Knowledge Assistant: Poisoned Document (Intermediate)

An internal knowledge assistant that answers employee questions by retrieving documents from a knowledge base. A poisoned document contains hidden instructions that trick the assistant into leaking the user's private API key. This scenario demonstrates **indirect prompt injection** — the attacker never interacts with the assistant directly.

- **Vulnerable mode:** No document sanitization, API key in same context as retrieved documents, no output filtering
- **Defended mode:** Document sanitization (strips HTML comments and injection patterns) + privilege separation (API key not in context) + output filtering (redacts credential patterns)
- **Attack families:** indirect_prompt_injection_context_data (~23 techniques), rag_specific_attack (~4 techniques)
- **OWASP mapping:** LLM01 — Prompt Injection (indirect)

## Security Notes

- PromptLab targets are **sandboxed Python functions**, not real LLM services
- The web UI can **only** target built-in scenarios -- no arbitrary URL input
- This is designed for **education and authorized security testing only**
- The sandbox runs deterministic simulations -- no LLM backend required for demos

## Current Limitations

- **Deterministic simulation only** -- sandbox targets use pattern matching, not a real LLM. Behaviour is realistic but not identical to production models.
- **Single-turn interactions** -- each simulation is one prompt/response pair. Multi-turn conversation support is planned.
- **Two scenarios** -- `support_bot` (direct injection) and `knowledge_assistant` (indirect injection). More scenarios are planned.
- **No adaptive attacks** -- techniques are fired as-is. TAP-style iterative refinement is reserved for a future release.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Backend HTTP port (Railway sets automatically) |
| `PROMPTLAB_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed CORS origins |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend API URL (build-time, set in Vercel) |

See [Deployment Guide](DEPLOYMENT.md) for full Railway + Vercel setup.

## Adding New Scenarios

1. Create target functions in `promptlab/scenarios/targets.py`
2. Register the scenario in `promptlab/scenarios/registry.py`
3. Add technique explanations for the relevant attack family
4. Add tests in `tests/promptlab/`
