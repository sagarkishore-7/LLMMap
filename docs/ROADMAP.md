# Roadmap — LLMMap + PromptLab

Last updated: 2026-03-18

---

## 1. Vision

**LLMMap** becomes the standard open-source engine for automated LLM red-teaming — a tool security teams use in CI pipelines, penetration tests, and model evaluations to systematically find prompt injection vulnerabilities before attackers do.

**PromptLab** becomes the interactive learning surface for LLM security — a place where developers, security engineers, and students can safely explore attack techniques, understand why they work, and learn to build defenses. It visualises what LLMMap does under the hood, without requiring a live LLM or a real target.

**How they connect:** PromptLab starts deterministic (sandbox simulations). Over time, it gains an optional "Real Mode" that calls the LLMMap engine against actual LLM backends. Users can compare deterministic simulations with real model behaviour side-by-side. The two systems share the same prompt library (227 techniques) and attack taxonomy, but PromptLab never becomes a general-purpose scanning tool — it stays educational, sandboxed, and safe.

---

## 2. Current State (v1.2.0)

### LLMMap CLI

- 227 prompt injection techniques across 18 attack families in 4 YAML packs
- Dual-LLM architecture: Generator crafts prompts, Judge evaluates responses
- 4 provider backends: Ollama Cloud (default), OpenAI, Anthropic, Google
- 5 injection point classes: query (Q), body (B), headers (H), cookies (C), path (P)
- Intensity levels 1–5 controlling prompts per family and obfuscation
- Wilson confidence interval for false-positive suppression
- Report export: JSON, Markdown, SARIF v2.1.0
- Burp Suite XML import, proxy support
- TAP (Tree of Attacks with Pruning) engine implemented
- OOB (Out-of-Band) canary support implemented
- Environment-driven configuration (Ollama Cloud default)

### PromptLab Web Lab

- 1 scenario: Support Bot with hidden system prompt (beginner)
- 6 curated technique explanations (instruction_manipulation family)
- Deterministic sandbox — no LLM calls, pattern-matching targets
- FastAPI backend with 5 REST endpoints
- Next.js frontend with scenario picker, chat visualisation, mode toggle, explanation panel
- Vulnerable vs. defended comparison in a single run
- Deployment-ready: Railway (backend) + Vercel (frontend)

### Test Coverage

- 123 tests total (91 LLMMap + 32 PromptLab)
- All tests pass on Python 3.13

### Key Constraints

- PromptLab is **stateless** — no sessions, no persistence, no user accounts
- PromptLab is **deterministic** — sandbox targets use pattern matching, not LLMs
- PromptLab **cannot scan external targets** from the web UI
- Frontend env vars (`NEXT_PUBLIC_*`) are build-time only

---

## 3. Architecture Principles

These principles govern all future development decisions:

1. **Deterministic-first for PromptLab.** Every scenario must work without an LLM backend. Real Mode is always optional, never required.

2. **Engine vs. product separation.** LLMMap is the engine (library, CLI). PromptLab is the product (web UI, API). They share prompt packs and attack taxonomy. They do not share runtime state.

3. **Environment-driven configuration.** No hardcoded URLs, keys, or model names. Everything configurable via env vars. Same codebase runs locally and in production.

4. **Sandbox constraints are permanent.** PromptLab's web UI will never accept arbitrary URLs or scan external targets. Scenarios are built-in. This is a safety invariant, not a limitation to remove later.

5. **Small increments, no breaking changes.** Each phase ships independently. New scenarios don't require API changes. New features don't break existing tests.

6. **Test-first where possible.** New scenarios come with tests. New engine features come with tests. Regressions are caught before merge.

---

## 4. Development Phases

### Phase 1 — PromptLab Foundation `COMPLETED`

- [x] Support Bot scenario (beginner, instruction_manipulation)
- [x] Deterministic sandbox targets (vulnerable + defended)
- [x] Simulation engine with heuristic judge
- [x] FastAPI REST API (5 endpoints)
- [x] Next.js frontend with chat, mode toggle, explanation panel
- [x] 6 curated technique explanations
- [x] 32 PromptLab tests
- [x] Report export pipeline (JSON, Markdown, SARIF)
- [x] Deployment readiness (Railway + Vercel)
- [x] Environment-driven configuration
- [x] Documentation (PROMPTLAB.md, DEPLOYMENT.md, ARCHITECTURE.md)

### Phase 2 — Scenario Expansion

Goal: expand PromptLab from 1 scenario to 3–4, covering distinct attack categories.

- [ ] **Knowledge Assistant** — indirect prompt injection via poisoned RAG documents (intermediate). Design spec complete at `docs/SCENARIO_KNOWLEDGE_ASSISTANT.md`.
- [ ] **Memory Bot** — multi-turn manipulation where earlier messages poison later responses (intermediate). Simulates conversation history injection without requiring actual multi-turn LLM calls.
- [ ] **Code Review Assistant** — injection via code comments or variable names that trigger the assistant to leak context (advanced). Demonstrates integration-surface attacks.
- [ ] Expand curated technique explanations to 20+ across multiple families
- [ ] Add scenario difficulty progression (beginner → intermediate → advanced)
- [ ] Add `indirect_prompt_injection_context_data`, `rag_specific_attack`, `cognitive_control_bypass`, and `agentic_pipeline` families to PromptLab

**System:** PromptLab
**Estimated scope per scenario:** ~300 lines (targets + registry + tests)
**API/UI changes:** None — dynamic discovery handles new scenarios automatically

### Phase 3 — Product Depth

Goal: make PromptLab feel like a polished product, not a prototype.

- [ ] **Run history** — in-memory history of simulations within a session (no backend persistence needed; frontend state)
- [ ] **Replay** — re-run a previous simulation with one click
- [ ] **Downloadable reports** — export simulation results as JSON or Markdown from the UI
- [ ] **Guided mode** — step-by-step walkthrough for first-time users explaining each panel
- [ ] **Technique browser** — standalone page to browse all 227 techniques by family, tags, and OWASP mapping without running a simulation
- [ ] **Comparison view** — side-by-side chat transcripts (vulnerable vs. defended) instead of toggle
- [ ] **Mobile-responsive layout** — current UI is desktop-focused

**System:** PromptLab (frontend-heavy)
**Backend changes:** Minimal — possibly a `/api/techniques` endpoint for the technique browser

### Phase 4 — Engine Maturity (LLMMap)

Goal: fill the gaps in the LLMMap CLI for real-world red-team engagements.

- [ ] **Model fingerprinting (Stage 0)** — identify target model family, version, and active guardrails before scanning. Use fingerprint results to prioritise techniques.
- [ ] **Multi-turn stateful attacks (Stage 2)** — crescendo attacks, codeword priming, gradual context shifting. Requires session/cookie tracking.
- [ ] **Indirect injection support** — inject prompts into data sources (documents, web pages, database records) that the target LLM retrieves during processing.
- [ ] **Budget and cost tracking** — token counting and spend limits for cloud providers. Abort/warn policy for runaway costs.
- [ ] **CI integration** — GitHub Actions workflow, exit codes for pipeline gating, SARIF upload to GitHub Code Scanning.
- [ ] **Improved TAP** — activate the TAP engine in the default scan pipeline (currently implemented but not wired into the standard flow).

**System:** LLMMap
**PromptLab impact:** None until Phase 5

### Phase 5 — PromptLab + LLMMap Integration

Goal: allow PromptLab to optionally call the LLMMap engine for live LLM interactions.

- [ ] **Real Mode** — new simulation mode alongside "vulnerable" and "defended". When enabled, the simulator calls a real LLM backend (via the LLMMap `LLMClient`) instead of the deterministic sandbox target.
- [ ] **Provider selection** — UI dropdown to choose Ollama Cloud, OpenAI, Anthropic, or Google. Reads API keys from backend env vars (never exposed to frontend).
- [ ] **Simulation vs. real comparison** — run the same technique in both deterministic and real mode, compare verdicts side-by-side. Shows where the simulation is accurate and where real models diverge.
- [ ] **Non-deterministic warning** — clear UI indicator when running in Real Mode. Results may vary between runs. Latency will be higher.
- [ ] **Rate limiting** — backend throttle for Real Mode to prevent abuse and cost overruns.
- [ ] **Response caching** — optional caching of real LLM responses to reduce costs during repeated demos.

**System:** Shared (PromptLab frontend + engine, LLMMap client)
**Key constraint:** Deterministic mode remains the default. Real Mode is opt-in.

### Phase 6 — Advanced Features

Goal: scale beyond individual use to team and enterprise contexts.

- [ ] **Plugin SDK** — stable interfaces for custom prompts, detectors, and guardrail classifiers. Third-party contributions without core engine changes.
- [ ] **Scenario packs** — downloadable bundles of scenarios for specific domains (healthcare, finance, code assistants).
- [ ] **Multimodal attacks** — hidden text in images (OCR), QR code prompts, audio transcription injection.
- [ ] **Guardrail benchmarking** — run a scenario against multiple models/guardrail configs and compare results. Which models are most resistant to which techniques?
- [ ] **Team features** — shared scenario results, team dashboards (requires persistence layer).

**System:** Both
**Dependency:** Phases 4 and 5 should be substantially complete first.

---

## 5. Detailed Feature Breakdown

### Phase 2 Features

| Feature | System | Description |
|---------|--------|-------------|
| Knowledge Assistant scenario | PromptLab | Indirect injection via poisoned RAG document. Secret: API key. Families: `indirect_prompt_injection_context_data`, `rag_specific_attack`. ~27 techniques. |
| Memory Bot scenario | PromptLab | Simulated multi-turn attack where injected context in "previous messages" poisons the assistant's response. Family: `cognitive_control_bypass`. |
| Code Review Assistant scenario | PromptLab | Injection via code comments/variable names in a code review context. Family: `integration_surface_attack`, `defense_evasion`. |
| Expanded explanations | PromptLab | 20+ curated explanations across `indirect_prompt_injection_context_data`, `rag_specific_attack`, `cognitive_control_bypass`, `agentic_pipeline`. |
| Difficulty progression | PromptLab | Landing page groups scenarios by difficulty. Visual badges already exist. |

### Phase 3 Features

| Feature | System | Description |
|---------|--------|-------------|
| Run history | PromptLab (frontend) | `useState` array of past SimulationResults. Sidebar or dropdown to revisit. No backend changes. |
| Replay | PromptLab (frontend) | Button on history entries to re-run with same parameters. |
| Downloadable reports | PromptLab | Frontend generates JSON/Markdown from SimulationResult and triggers browser download. No backend changes. |
| Guided mode | PromptLab (frontend) | Overlay tooltips explaining each UI section. First-run detection via localStorage. |
| Technique browser | PromptLab | New `/techniques` page. Needs backend `/api/techniques` endpoint listing all 227 techniques with family, tags, and explanation status. |
| Comparison view | PromptLab (frontend) | Two-column chat layout replacing the toggle. Both transcripts visible simultaneously. |

### Phase 4 Features

| Feature | System | Description |
|---------|--------|-------------|
| Model fingerprinting | LLMMap | Stage 0 pre-scan phase. Sends diagnostic prompts to identify model family, version, guardrail config. Results stored in run metadata. |
| Multi-turn attacks | LLMMap | Stage 2 pipeline. Conversation state tracked via session cookies/headers. Techniques: crescendo, codeword priming, context shifting. |
| Indirect injection | LLMMap | New injection point class for document/data-source injection. Requires target-specific integration (e.g., file upload, API endpoint). |
| Budget tracking | LLMMap | Token counter per provider. Configurable `--max-cost` flag. Warn/abort policy. |
| CI integration | LLMMap | `llmmap --ci` mode: exit code 1 if findings, SARIF auto-upload, minimal console output. |
| TAP activation | LLMMap | Wire TAP engine into the standard scan pipeline as an optional `--tap` flag. Currently implemented but isolated. |

### Phase 5 Features

| Feature | System | Description |
|---------|--------|-------------|
| Real Mode | Shared | New `mode: "real_vulnerable"` / `mode: "real_defended"` values. Simulator instantiates `LLMClient` and sends the attack prompt to a real model. |
| Provider selection | PromptLab | UI dropdown in attack controls panel. Backend reads `OLLAMA_API_KEY` / `OPENAI_API_KEY` etc. from env. |
| Sim vs. real comparison | PromptLab (frontend) | Third tab alongside Vulnerable/Defended showing real model response. |
| Non-deterministic warning | PromptLab (frontend) | Badge + disclaimer when Real Mode is active. |
| Rate limiting | PromptLab (backend) | FastAPI middleware or dependency. Per-IP or global limit on `/api/simulate` when mode is real. |
| Response caching | PromptLab (backend) | Hash of (scenario_id, technique_id, mode, provider, model) → cached response. TTL-based expiry. |

---

## 6. Immediate Next Tasks

These are the next 10 concrete tasks in priority order:

### 6.1 Implement `knowledge_assistant` scenario

**Description:** Build the indirect prompt injection scenario following the design spec in `docs/SCENARIO_KNOWLEDGE_ASSISTANT.md`. Poisoned RAG document causes the assistant to leak a user's API key.

**Affected files:**
- `promptlab/scenarios/targets.py` — add target functions, documents, system prompts, sanitiser
- `promptlab/scenarios/registry.py` — register scenario + 6 curated explanations
- `tests/promptlab/test_scenarios.py` — 7 new tests
- `tests/promptlab/test_simulator.py` — 6 new tests
- `tests/promptlab/test_api.py` — 4 new tests
- `docs/PROMPTLAB.md` — add scenario description

**Expected outcome:** 2 scenarios in the landing page. All 140+ tests pass. No API/UI/schema changes.

### 6.2 Add simulation metadata to API response

**Description:** Include `simulation_mode: "deterministic"` in the `SimulateResponse` so the frontend can display it. This prepares the API contract for Real Mode later.

**Affected files:**
- `promptlab/engine/schemas.py` — add `simulation_mode` field to `SimulationResult`
- `promptlab/api/main.py` — add field to `SimulateResponse`

**Expected outcome:** API responses include `"simulation_mode": "deterministic"`. Frontend can display "Sandboxed simulation" badge.

### 6.3 Display simulation mode badge in frontend

**Description:** Show a small "Deterministic Simulation" badge in the lab view header, next to the existing "Sandboxed" badge. Uses the `simulation_mode` field from 6.2.

**Affected files:**
- `web/app/page.tsx`

**Expected outcome:** Users always know they're seeing a simulation, not real LLM output.

### 6.4 Add `/api/techniques` endpoint

**Description:** New endpoint that lists all 227 techniques with family, tags, and explanation status — independent of any scenario. Prepares for the technique browser page.

**Affected files:**
- `promptlab/api/main.py` — new route
- `promptlab/engine/simulator.py` — new `list_all_techniques()` function
- `tests/promptlab/test_api.py` — new tests

**Expected outcome:** `GET /api/techniques` returns full technique catalog.

### 6.5 Improve explanation panel consistency

**Description:** Ensure all 22 `instruction_manipulation` techniques have curated explanations (currently 6 of 22). Expand coverage so users see specific content more often than the fallback.

**Affected files:**
- `promptlab/scenarios/registry.py` — add 16 more `TechniqueExplanation` entries

**Expected outcome:** 22 curated explanations for the full `instruction_manipulation` family.

### 6.6 Design Memory Bot scenario

**Description:** Write a design spec (like `SCENARIO_KNOWLEDGE_ASSISTANT.md`) for a multi-turn manipulation scenario. The attacker poisons simulated conversation history to manipulate the assistant's response.

**Affected files:**
- `docs/SCENARIO_MEMORY_BOT.md` (new)

**Expected outcome:** Complete design spec ready for implementation.

### 6.7 Add frontend run history (in-memory)

**Description:** Store simulation results in React state so users can revisit past runs within the same session. No backend persistence needed.

**Affected files:**
- `web/app/page.tsx`

**Expected outcome:** Sidebar or dropdown showing previous runs. Clicking one restores the full result view.

### 6.8 Create demo assets

**Description:** Record a GIF or screenshot walkthrough of PromptLab showing: landing page → select scenario → run simulation → view vulnerable result → toggle to defended → read explanation panel.

**Affected files:**
- `assets/` — new screenshot/GIF files
- `README.md` — update hero image to show PromptLab

**Expected outcome:** Repository has a compelling visual that shows what PromptLab does.

### 6.9 Add CI workflow

**Description:** GitHub Actions workflow that runs `pytest` and `next build` on push/PR. Ensures regressions are caught before merge.

**Affected files:**
- `.github/workflows/ci.yml` (new)

**Expected outcome:** PRs show green/red test status. Frontend build failures are caught.

### 6.10 Wire TAP engine into LLMMap CLI

**Description:** Add `--tap` flag to the CLI that activates the Tree of Attacks with Pruning engine (already implemented in `llmmap/core/tap.py`). This is the highest-impact LLMMap improvement.

**Affected files:**
- `llmmap/cli.py` — new `--tap` flag
- `llmmap/core/orchestrator.py` — conditional TAP activation
- `tests/test_cli.py` — new tests

**Expected outcome:** `llmmap -r request --goal "..." --tap` uses iterative prompt refinement.

---

## 7. Integration Plan (PromptLab ↔ LLMMap)

### Current State

PromptLab and LLMMap share:
- **Prompt packs** — PromptLab loads techniques from `llmmap/prompts/packs/`
- **Rendering engine** — PromptLab uses `llmmap.prompts.render` to build attack prompts
- **Technique selector** — PromptLab uses `llmmap.prompts.selector` to filter by family

They do **not** share:
- LLM client — PromptLab never calls `llmmap.llm.client.LLMClient`
- HTTP engine — PromptLab never sends real HTTP requests
- Judge — PromptLab uses its own deterministic heuristic judge, not LLMMap's LLM judge

### Integration Steps

**Step 1: API contract preparation (Phase 2)**

Add `simulation_mode` field to `SimulationResult` and `SimulateResponse`. Values: `"deterministic"` (current), `"live"` (future). This is backward-compatible — existing clients ignore the new field.

**Step 2: LLM client injection point (Phase 5)**

Modify `promptlab/engine/simulator.py` to accept an optional `LLMClient` instance:

```python
def run_simulation(
    scenario_id: str,
    technique_id: str,
    mode: str,
    llm_client: LLMClient | None = None,  # None = deterministic
) -> SimulationResult:
```

When `llm_client` is provided:
- The attack prompt is sent to the real LLM instead of the sandbox target
- The judge uses the LLM judge instead of heuristics
- `simulation_mode` is set to `"live"`

When `llm_client` is `None` (default):
- Current deterministic behaviour is unchanged
- Zero LLM calls, zero cost, zero latency

**Step 3: Backend provider config (Phase 5)**

Add a `POST /api/simulate` parameter `real_mode: bool = False`. When `True`:
- Backend instantiates `LLMClient` from env vars (`OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, etc.)
- Passes it to `run_simulation()`
- Returns response with `simulation_mode: "live"`

Rate limiting and API key validation happen at this layer.

**Step 4: Frontend Real Mode toggle (Phase 5)**

Add a toggle in the attack controls panel. When enabled:
- Sends `real_mode: true` in the simulate request
- Displays "Live LLM" badge instead of "Deterministic Simulation"
- Shows latency and token count in the verdict card
- Warns that results may vary between runs

### Safety Invariants

- Deterministic mode is always the default
- Real Mode requires explicit opt-in (both API parameter and UI toggle)
- Real Mode only targets the LLM backend, never external URLs
- API keys are never exposed to the frontend
- Rate limiting is mandatory in Real Mode

---

## 8. Constraints and Non-Goals

### Constraints

- **No external scanning from PromptLab.** The web UI targets only built-in sandbox scenarios. This is a permanent safety boundary.
- **Deterministic simulation is the foundation.** Every scenario must work without an LLM. Real Mode is supplementary.
- **No premature microservices.** PromptLab is a single FastAPI app. LLMMap is a CLI. They share a Python package. No message queues, no containers, no orchestration.
- **No early over-reliance on LLMs.** PromptLab's value comes from the technique library, educational content, and visualisation — not from live model output.

### Non-Goals

- **PromptLab is not a general-purpose LLM testing tool.** It is educational. LLMMap CLI is the tool for real engagements.
- **No user accounts or authentication.** PromptLab is a single-user tool. Multi-tenancy is Phase 6+ and may not be needed.
- **No custom scenario creation from the UI.** Scenarios are code — defined in Python, registered in the catalog. There is no scenario editor.
- **No model training or fine-tuning.** LLMMap tests models. It does not train them.
- **No bounty automation.** LLMMap is for authorised testing with prior consent. It is not designed for automated vulnerability hunting at scale.

---

## 9. Success Metrics

| Metric | Phase 2 Target | Phase 3 Target | Phase 5 Target |
|--------|---------------|----------------|----------------|
| Scenarios | 3–4 | 5+ | 5+ (with Real Mode) |
| Curated explanations | 30+ | 50+ | 50+ |
| Total tests | 160+ | 180+ | 200+ |
| Attack families in PromptLab | 4+ | 6+ | 8+ |
| Time to first simulation (new user) | < 30 seconds | < 20 seconds | < 20 seconds |
| Frontend build time | < 30 seconds | < 30 seconds | < 30 seconds |
| API response time (deterministic) | < 100ms | < 100ms | < 100ms |
| Demo quality | Working demo | Guided walkthrough | Side-by-side real vs. sim |
| CI pipeline | Manual | Automated (GitHub Actions) | Automated |

---

## 10. Contribution Guide

### How to add a scenario

1. Write a design spec in `docs/SCENARIO_<NAME>.md` following the Knowledge Assistant template.
2. Implement target functions in `promptlab/scenarios/targets.py` (vulnerable + defended pair).
3. Register the scenario in `promptlab/scenarios/registry.py` with curated technique explanations.
4. Update `get_scenario_secret()` in `targets.py`.
5. Add tests to all three test files (`test_scenarios.py`, `test_simulator.py`, `test_api.py`).
6. Update `docs/PROMPTLAB.md` with the scenario description.
7. Run `pytest` — all existing tests must pass.

No API, schema, or UI changes are needed. The frontend discovers scenarios dynamically.

### How to add a technique explanation

1. Find the technique ID in the YAML packs (`llmmap/prompts/packs/`).
2. Add a `TechniqueExplanation` entry to `TECHNIQUE_EXPLANATIONS` in `promptlab/scenarios/registry.py`.
3. Include: `technique_id`, `family`, `name`, `description`, `owasp_tag`, `why_it_works`, `how_to_mitigate`.

### Development practices

- **Small increments.** One scenario per PR. One feature per PR. Don't bundle unrelated changes.
- **Test-first where possible.** Write the test for the scenario behaviour before implementing the target.
- **No breaking changes.** New scenarios, new endpoints, new fields — always additive. Don't rename existing API fields or remove working features.
- **Follow roadmap order.** Phase 2 before Phase 3. Scenario expansion before product depth. Engine maturity and integration happen last.
- **Document before implementing.** Design specs prevent scope creep and make review easier.
