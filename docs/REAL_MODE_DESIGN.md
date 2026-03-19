# Design Spec — PromptLab Real Mode Integration

**Status:** Draft
**Phase:** 5 (per `docs/ROADMAP.md`)
**Author:** Design-only — no code changes
**Last updated:** 2026-03-20

---

## 1. Goals and Non-Goals

### Goals

- Allow PromptLab users to optionally run simulations against a **real LLM backend** instead of the deterministic sandbox target.
- Let users compare deterministic vs. live results for the same technique/scenario pair, reinforcing PromptLab's educational mission ("does the real model behave like the simulation predicted?").
- Reuse the existing `LLMClient` from `llmmap.llm.client` — no new HTTP/provider code.
- Keep the implementation surface small: one new parameter on the simulate API, one new code path in the simulator, one new toggle in the frontend.

### Non-Goals

- **Not a general scanning tool.** Real Mode targets only server-configured LLM backends, never arbitrary URLs.
- **Not multi-turn.** Real Mode sends a single attack prompt and receives a single response, matching the existing simulation shape. Multi-turn attacks are a separate LLMMap engine feature (Phase 4).
- **Not a model evaluation harness.** No batch runs, no statistical aggregation, no benchmarking tables. One technique, one run, one result.
- **No user accounts, API key input, or persistence.** API keys live in backend env vars. Results are ephemeral (frontend state only), matching current behavior.
- **No custom model parameters.** Users cannot set temperature, max tokens, or system prompts from the UI. Sane defaults are chosen server-side.

---

## 2. Deterministic Mode Remains Default

This is the most important architectural invariant.

| Property | Deterministic (current) | Real Mode (new) |
|---|---|---|
| Default | Yes — always | No — explicit opt-in |
| LLM dependency | None | Requires configured backend |
| Cost | Zero | Per-token charges (provider-dependent) |
| Latency | < 100ms | 1–10 seconds |
| Reproducibility | Identical every run | Non-deterministic |
| Availability | Always works | Fails if backend is down or unconfigured |

**Enforcement rules:**

1. If `real_mode` is not explicitly set to `true` in the API request, the simulator uses the deterministic path. No fallback from deterministic to real.
2. If `real_mode=true` but no LLM backend is configured, the API returns `HTTP 503` with a clear error — it does not silently fall back to deterministic.
3. The frontend defaults the Real Mode toggle to OFF. It never auto-enables.
4. The landing page, guided tour, and all documentation describe PromptLab as a deterministic sandbox first. Real Mode is presented as an advanced, optional comparison tool.

---

## 3. How Real Mode Calls Into LLMMap

### Architecture

```
Frontend                    Backend (FastAPI)                 LLMMap
────────                    ────────────────                 ──────
POST /api/simulate    →     simulate() handler
  real_mode: true           │
                            ├─ build attack prompt           llmmap.prompts.render
                            ├─ instantiate LLMClient         llmmap.llm.client
                            ├─ send system_prompt + attack   LLMClient.chat()
                            ├─ receive LLM response
                            ├─ judge response                (heuristic or LLM judge)
                            └─ return SimulateResponse
                                simulation_mode: "live"
```

### Simulator changes (`promptlab/engine/simulator.py`)

The `run_simulation()` function gains an optional `llm_client` parameter:

```python
def run_simulation(
    scenario_id: str,
    technique_id: str,
    mode: str,
    llm_client: LLMClient | None = None,
) -> SimulationResult:
```

When `llm_client is not None`:

1. **Attack prompt** — built identically to deterministic mode (`_build_attack_prompt`). Same technique template, same rendering.
2. **Target call** — instead of `target_fn(attack_prompt)`, call:
   ```python
   response_text = llm_client.chat(
       system_prompt=scenario.system_prompt,
       user_message=attack_prompt,
       temperature=0.0,
       timeout=30.0,
   )
   ```
   The scenario's system prompt (currently only visible post-simulation) becomes the actual LLM system prompt.
3. **Transcript** — built from the real system prompt, attack prompt, and LLM response. Same `ChatMessage` structure.
4. **Judge** — the deterministic heuristic judge runs first (same `_judge_response`). The secret-matching path still works because the scenario secret is known. In a future iteration, the LLM judge from `llmmap.detectors.judge` could be used as a secondary signal, but this is not required for the initial implementation.
5. **Result** — `simulation_mode` is set to `"live"` instead of `"deterministic"`.

When `llm_client is None` (default):

- **Zero changes** to the current code path.

### Why this shape

- The simulator already builds the attack prompt and judges the response. Real Mode only replaces the middle step (sandbox target → LLM call).
- `LLMClient` is a clean, stateless interface: `chat(system_prompt, user_message) → str`. No session management, no streaming, no callbacks.
- The scenario's system prompt is already stored in the registry and returned post-simulation. Sending it to a real LLM is a natural extension.

---

## 4. API Contract Changes

### `POST /api/simulate` — request

Add one optional field to `SimulateRequest`:

```python
class SimulateRequest(BaseModel):
    scenario_id: str
    technique_id: str
    mode: str  # "vulnerable" or "defended"
    real_mode: bool = False  # NEW — opt-in to live LLM
```

The `mode` field retains its current meaning: `"vulnerable"` uses the scenario's base system prompt, `"defended"` uses the hardened system prompt. This applies equally to deterministic and real mode.

### `POST /api/simulate` — response

No structural changes. The existing `SimulateResponse` already has `simulation_mode: str`. Values:

| `simulation_mode` | Meaning |
|---|---|
| `"deterministic"` | Sandbox target (current) |
| `"live"` | Real LLM backend |

One new optional field for cost transparency:

```python
class SimulateResponse(BaseModel):
    # ... existing fields ...
    simulation_mode: str = "deterministic"
    latency_ms: int | None = None        # NEW — wall-clock time of LLM call
    provider: str | None = None           # NEW — e.g. "ollama", "openai"
    model: str | None = None              # NEW — e.g. "gpt-4o-mini"
```

These fields are `None` in deterministic mode, populated in live mode.

### `GET /api/real-mode/status` — new endpoint

A lightweight endpoint the frontend calls once on page load to determine whether Real Mode is available:

```python
@app.get("/api/real-mode/status")
def real_mode_status() -> dict:
    return {
        "available": bool(configured_provider),
        "provider": configured_provider_name or None,
        "model": configured_model_name or None,
    }
```

If `available` is `false`, the frontend hides the Real Mode toggle entirely. No confusing disabled buttons.

---

## 5. Backend Provider Configuration

### Environment variables

Real Mode reuses the same env vars that LLMMap CLI already reads:

| Variable | Purpose | Example |
|---|---|---|
| `PROMPTLAB_REAL_MODE` | Master switch — `"true"` to enable | `true` |
| `PROMPTLAB_LLM_PROVIDER` | Provider name | `ollama`, `openai`, `anthropic`, `google` |
| `PROMPTLAB_LLM_MODEL` | Model identifier | `qwen3-coder-next:cloud`, `gpt-4o-mini` |
| `OLLAMA_BASE_URL` | Ollama endpoint | `https://api.ollama.com` |
| `OLLAMA_API_KEY` | Ollama Cloud API key | `olk_...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google API key | `AIza...` |

### Provider resolution

At startup, the backend:

1. Checks `PROMPTLAB_REAL_MODE == "true"`. If not set or `"false"`, Real Mode is disabled — no LLMClient is instantiated, `/api/real-mode/status` returns `available: false`.
2. Reads `PROMPTLAB_LLM_PROVIDER` and `PROMPTLAB_LLM_MODEL`.
3. Resolves the API key from the provider-specific env var.
4. Instantiates a single `LLMClient` instance at app startup (or lazily on first request).
5. Calls `client.check_connectivity()` to validate the backend is reachable.

### Why separate `PROMPTLAB_*` vars

The LLMMap CLI has its own provider resolution logic tied to `RuntimeConfig`. PromptLab should not couple to that — it needs explicit, independent configuration. A deployment might run PromptLab against a cheap model (`gpt-4o-mini`) while LLMMap CLI scans use a different model.

---

## 6. Frontend UX Changes

### Real Mode toggle

Add a toggle in the **Attack Configuration** panel (below the technique dropdown, beside the "Run Simulation" button):

```
┌─ Attack Configuration ──────────────────────────────────────────┐
│  Technique: [Direct Instruction Override ▼]                     │
│                                                                 │
│  ☐ Real Mode (gpt-4o-mini via OpenAI)     [▶ Run Simulation]   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

- **Hidden** when `/api/real-mode/status` returns `available: false`.
- **Unchecked** by default.
- Shows provider + model name inline so the user knows what they're hitting.
- When checked, the "Run Simulation" button text changes to "Run Live Simulation" with an amber accent to signal cost/latency implications.

### Header badge

When Real Mode is active, replace the "Deterministic" badge with:

```
⚡ Live LLM (gpt-4o-mini)
```

Amber color scheme to distinguish from the green "Sandboxed" badge and the blue "Deterministic" badge.

### Comparison view

The existing side-by-side layout (vulnerable vs. defended) works unchanged. Both panels show either deterministic or live results depending on the toggle. The simulation_mode badge tells the user which mode produced the current results.

**Future enhancement (not in scope for initial implementation):** A third comparison axis — deterministic vs. live for the same mode — showing where the simulation diverges from real model behavior. This would require running 4 simulations (det-vuln, det-def, live-vuln, live-def) and a more complex layout.

### Loading state

Real Mode calls take 1–10 seconds. The existing spinner and "Running..." state handle this. Add a subtle "Waiting for LLM response..." label when `real_mode` is active to set latency expectations.

### Verdict card additions

When `simulation_mode === "live"`, show below the verdict:

- **Latency:** `{latency_ms}ms`
- **Provider:** `{provider} / {model}`
- **Warning:** "Results may vary between runs. This is a live LLM response, not a deterministic simulation."

---

## 7. Safety Constraints and Rate Limiting

### Rate limiting

| Scope | Limit | Rationale |
|---|---|---|
| Per-IP, Real Mode | 10 requests / minute | Prevents runaway costs from a single client |
| Global, Real Mode | 60 requests / minute | Caps total LLM spend across all users |
| Deterministic mode | No limit | Zero cost, instant response |

Implementation: FastAPI dependency using an in-memory sliding window counter. No external Redis dependency.

```python
from fastapi import Depends

async def check_real_mode_rate_limit(request: Request):
    # Sliding window counter keyed by client IP
    ...
```

### Safety invariants

1. **No arbitrary targets.** The `real_mode` flag sends the attack to the configured LLM backend, not to a user-supplied URL. The `SimulateRequest` schema has no URL field and must never gain one.
2. **API keys never reach the frontend.** The `/api/real-mode/status` endpoint returns provider name and model name, never the key. The `SimulateResponse` includes provider/model for display, never the key.
3. **Scenario system prompts only.** Real Mode uses the scenario's built-in system prompt, not a user-supplied one. This prevents the web UI from being used as a general-purpose LLM proxy.
4. **Mode validation.** The `mode` field is still restricted to `"vulnerable"` or `"defended"`. No new mode values are added.
5. **Timeout.** LLM calls have a 30-second hard timeout. If the backend is slow or unresponsive, the request fails cleanly instead of hanging.
6. **No streaming.** Responses are returned complete, not streamed. This simplifies the security boundary and avoids partial-response edge cases.

---

## 8. Caching and Cost Control

### Response caching

Cache key: `(scenario_id, technique_id, mode, provider, model)`

Cache behavior:
- **TTL:** 1 hour. LLM responses to the same prompt are similar but not identical. Caching reduces cost for repeated demos without hiding non-determinism entirely.
- **Storage:** In-memory `dict` with TTL eviction. No external cache dependency.
- **Cache hit:** Return cached response with `simulation_mode: "live_cached"` so the frontend can indicate staleness.
- **Cache bypass:** Add optional `bypass_cache: bool = False` to `SimulateRequest` for users who want a fresh response.
- **Cache scope:** Per-process. Restarting the backend clears the cache. This is intentional — no stale data across deployments.

### Cost control

| Mechanism | Description |
|---|---|
| Rate limiting | Per-IP and global limits (see §7) |
| Single-turn only | No multi-turn conversations — one LLM call per simulation |
| Temperature 0.0 | Minimizes response variance, improves cache hit rate |
| Timeout | 30s hard cap prevents runaway requests |
| No streaming | Prevents long-lived connections |
| Admin kill switch | `PROMPTLAB_REAL_MODE=false` disables instantly, no restart needed if using a config watcher (future) |

### Cost estimation

Assuming `gpt-4o-mini` pricing (~$0.15/1M input, ~$0.60/1M output):
- Average attack prompt: ~200 tokens input, ~150 tokens output
- Cost per simulation: ~$0.0001 (0.01 cents)
- 60 requests/minute global cap: ~$0.36/hour maximum

---

## 9. Data Model Additions

### `promptlab/engine/schemas.py`

```python
@dataclass
class SimulationResult:
    # ... existing fields unchanged ...
    simulation_mode: str = "deterministic"
    latency_ms: int | None = None          # NEW
    provider: str | None = None             # NEW
    model: str | None = None                # NEW
```

### `promptlab/api/main.py`

```python
class SimulateRequest(BaseModel):
    # ... existing fields unchanged ...
    real_mode: bool = False                  # NEW

class SimulateResponse(BaseModel):
    # ... existing fields unchanged ...
    simulation_mode: str = "deterministic"
    latency_ms: int | None = None           # NEW
    provider: str | None = None             # NEW
    model: str | None = None                # NEW
```

### Frontend types (`web/app/page.tsx`)

```typescript
interface SimulationResult {
  // ... existing fields unchanged ...
  simulation_mode?: string;
  latency_ms?: number | null;     // NEW
  provider?: string | null;       // NEW
  model?: string | null;          // NEW
}
```

### No new database tables, files, or persistence layers.

---

## 10. How Results Differ Between Modes

| Aspect | Deterministic | Live |
|---|---|---|
| `simulation_mode` | `"deterministic"` | `"live"` (or `"live_cached"`) |
| Response source | Pattern-matching sandbox target | Real LLM API call |
| System prompt | Used by sandbox logic internally | Sent as actual LLM system prompt |
| Response content | Scripted — same every time | Model-generated — varies per run |
| Verdict method | `"deterministic"` or `"heuristic"` | `"heuristic"` (same judge, real data) |
| Secret detection | Exact match (secret is known) | Exact match still works — secret is known |
| Latency | < 100ms | 1–10 seconds |
| Cost | Zero | Per-token (provider-dependent) |
| `latency_ms` | `null` | Populated |
| `provider` / `model` | `null` | Populated |

### Educational value of the difference

The key insight for users: **deterministic simulations model the worst case** (vulnerable target always leaks, defended target always blocks). Real models sit somewhere in between — sometimes the attack works, sometimes the model's built-in guardrails catch it. Comparing both teaches users:

1. Which techniques are effective in theory vs. practice
2. How much variance exists in real model behavior
3. Why defense-in-depth matters even when the model seems robust

---

## 11. Migration Plan / Phased Rollout

### Phase 5a — Backend wiring (no frontend)

1. Add `real_mode: bool = False` to `SimulateRequest`.
2. Add `PROMPTLAB_REAL_MODE` / `PROMPTLAB_LLM_PROVIDER` / `PROMPTLAB_LLM_MODEL` env vars.
3. Add `LLMClient` instantiation at startup (guarded by env vars).
4. Add `llm_client` parameter to `run_simulation()`.
5. Add `/api/real-mode/status` endpoint.
6. Add rate limiting middleware for real mode requests.
7. Add response caching.
8. Add tests: unit tests with mocked `LLMClient`, integration test with a local Ollama instance (optional, CI-skippable).

**Deliverable:** Real Mode works via `curl` / API client. Frontend is unchanged.

### Phase 5b — Frontend toggle

1. Fetch `/api/real-mode/status` on page load.
2. Conditionally render Real Mode toggle.
3. Pass `real_mode: true` in simulate request when toggle is on.
4. Display live-mode badges, latency, provider info.
5. Add "Waiting for LLM response..." loading variant.
6. Update export (JSON/Markdown) to include new fields.

**Deliverable:** Full end-to-end Real Mode from the UI.

### Phase 5c — Polish

1. Cache hit indicator in the UI (`"live_cached"` badge).
2. "Try with a different model" — if multiple providers are configured, allow selection (stretch goal).
3. Documentation update: `docs/PROMPTLAB.md`, `docs/DEPLOYMENT.md`.

### Rollback

At any point, setting `PROMPTLAB_REAL_MODE=false` (or removing the env var) disables Real Mode entirely. The frontend hides the toggle, the API rejects `real_mode: true` requests with `503`. Zero code changes needed to roll back.

---

## 12. Test Strategy

### Unit tests (`tests/promptlab/test_simulator.py`)

| Test | Description |
|---|---|
| `test_real_mode_uses_llm_client` | Mock `LLMClient.chat()`, verify it's called with scenario system prompt + attack prompt |
| `test_real_mode_sets_simulation_mode_live` | Verify `simulation_mode == "live"` in result |
| `test_real_mode_populates_latency` | Verify `latency_ms` is a positive integer |
| `test_real_mode_populates_provider_model` | Verify `provider` and `model` match config |
| `test_deterministic_mode_unchanged` | Existing tests still pass with `llm_client=None` |
| `test_real_mode_heuristic_judge_on_real_response` | Judge correctly detects secrets in LLM output |
| `test_real_mode_defended_uses_defended_prompt` | Defended system prompt is sent to LLM, not vulnerable |

### API tests (`tests/promptlab/test_api.py`)

| Test | Description |
|---|---|
| `test_simulate_real_mode_disabled_returns_503` | When `PROMPTLAB_REAL_MODE` is unset, `real_mode: true` returns 503 |
| `test_simulate_real_mode_default_false` | Request without `real_mode` field runs deterministic |
| `test_real_mode_status_endpoint_available` | `/api/real-mode/status` returns expected shape |
| `test_real_mode_status_unavailable` | When unconfigured, returns `available: false` |
| `test_real_mode_rate_limit` | 11th request in 1 minute returns 429 |

### Integration tests (optional, CI-skippable)

| Test | Description |
|---|---|
| `test_real_mode_ollama_local` | Against a local Ollama instance. Skip if unavailable. |
| `test_real_mode_round_trip` | Full API call with mocked LLMClient, verify response shape. |

### Frontend tests (manual checklist)

- [ ] Toggle hidden when Real Mode unavailable
- [ ] Toggle visible when Real Mode available
- [ ] Toggle defaults to OFF
- [ ] "Run Live Simulation" button text when toggle is ON
- [ ] Live badge appears in header
- [ ] Latency and provider shown in verdict card
- [ ] Export includes new fields
- [ ] Spinner shows "Waiting for LLM response..."

---

## 13. Risks and Limitations

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Cost overrun** from unthrottled Real Mode | Medium | High | Rate limiting (§7), TTL cache (§8), global cap |
| **LLM backend downtime** degrades UX | Medium | Low | `/api/real-mode/status` hides toggle when unavailable; deterministic mode unaffected |
| **Model refuses all attacks** (strong guardrails) | High | Medium | Expected behavior — educational value is in showing that defenses work. Verdict will read "blocked" with heuristic confidence. |
| **Model leaks in defended mode** (weak guardrails) | Medium | Medium | Also educational — shows that Real Mode defended results may differ from deterministic predictions. Document this in the UI. |
| **Prompt injection of the PromptLab backend itself** | Low | Medium | PromptLab does not use LLM output for any control flow. Responses are displayed as text only. No tool use, no code execution, no downstream actions. |
| **API key exposure** | Low | High | Keys in env vars only. Never in API responses, frontend code, or logs. `provider` and `model` strings are safe to expose. |

### Limitations

1. **Single-turn only.** Real Mode sends one message and receives one response. Multi-turn attacks (crescendo, codeword priming) are not supported. This matches the existing simulation shape.
2. **No model selection from UI** (initial version). The backend uses one configured provider/model. Multi-model comparison is a Phase 5c stretch goal.
3. **Heuristic judge only.** The LLM judge from `llmmap.detectors.judge` is not used in the initial implementation. Heuristic judging works because scenario secrets are known. LLM judging is a future enhancement for more nuanced verdict reasoning.
4. **No token counting.** `LLMClient.chat()` returns only the response text, not token usage metadata. Cost estimation is approximate. Adding token counts requires provider-specific response parsing changes in `llmmap/llm/providers.py`.
5. **Cache is per-process.** Multiple backend workers (e.g., behind gunicorn) each have independent caches. Acceptable for the expected deployment scale.
6. **No offline mode.** If the LLM backend is unreachable and Real Mode is toggled on, the user sees an error. There is no automatic fallback to deterministic — this is intentional to avoid confusion about which mode produced the result.

---

## Appendix A — File Change Inventory

| File | Change Type | Description |
|---|---|---|
| `promptlab/engine/simulator.py` | Modify | Add `llm_client` param to `run_simulation()`, live code path |
| `promptlab/engine/schemas.py` | Modify | Add `latency_ms`, `provider`, `model` fields to `SimulationResult` |
| `promptlab/api/main.py` | Modify | Add `real_mode` to request, new fields to response, `/api/real-mode/status`, rate limiting |
| `promptlab/api/rate_limit.py` | New | Sliding window rate limiter (in-memory) |
| `promptlab/api/llm_provider.py` | New | Startup LLMClient instantiation from env vars |
| `web/app/page.tsx` | Modify | Real Mode toggle, live badges, latency display |
| `tests/promptlab/test_simulator.py` | Modify | Real Mode unit tests |
| `tests/promptlab/test_api.py` | Modify | Real Mode API tests, rate limit tests |
| `docs/PROMPTLAB.md` | Modify | Document Real Mode |
| `docs/DEPLOYMENT.md` | Modify | Document new env vars |

## Appendix B — Sequence Diagram

```
User clicks "Run Live Simulation"
    │
    ▼
Frontend POST /api/simulate { real_mode: true, scenario_id, technique_id, mode }
    │
    ▼
Backend: check rate limit
    │ (over limit → 429)
    ▼
Backend: check cache for (scenario_id, technique_id, mode, provider, model)
    │ (hit → return cached with simulation_mode: "live_cached")
    ▼
Backend: build_attack_prompt(technique_id, scenario.goal)
    │
    ▼
Backend: llm_client.chat(scenario.system_prompt, attack_prompt)
    │                            │
    │                            ▼
    │                    LLM Provider API
    │                            │
    │                            ▼
    │                    LLM response text
    ▼
Backend: _judge_response(response_text, goal, scenario_id)
    │
    ▼
Backend: build SimulationResult(simulation_mode="live", latency_ms=..., provider=..., model=...)
    │
    ▼
Backend: cache result, return SimulateResponse
    │
    ▼
Frontend: display with live badge, latency, provider info
```
