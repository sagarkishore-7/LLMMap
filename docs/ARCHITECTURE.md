# Architecture -- LLMMap v1.1.0

## Overview

LLMMap is an automated prompt injection testing framework inspired by sqlmap. It operates in a stateless fire-and-judge loop: each prompt is injected independently into one or more discovered injection points, the target response is diffed against a clean baseline, and an LLM judge scores whether the attacker-specified goal was achieved. Confirmed findings are emitted only after passing a reliability gate based on repeated independent probes.

## Package Layout

```
llmmap/
    __init__.py
    cli.py                          # argparse-based argument parser and entry point
    config.py                       # RuntimeConfig dataclass (all scan settings)

    core/
        __init__.py
        scanner.py                  # Top-level scan pipeline (run_scan)
        orchestrator.py             # Main probe loop and finding confirmation
        http_client.py              # HTTP execution engine (urllib.request)
        request_loader.py           # Burp Suite XML and URL-based request loading
        injection_points.py         # Injection point discovery (Q/B/H/C/P)
        request_mutator.py          # Prompt injection into request copies
        goal_judge.py               # LLM-based goal achievement scoring
        prompt_generator.py         # LLM prompt generation from style templates
        reliability.py              # Retry logic and Wilson confidence interval
        models.py                   # Evidence, Finding, ScanReport data types
        ui.py                       # Console output (banner, markers, findings block)
        run.py                      # Run workspace creation and metadata
        audit.py                    # Audit trail logging
        sensitive.py                # Sensitive data detection in responses
        pattern_detection.py        # Response pattern matching heuristics
        dataflow.py                 # Internal data-flow tracing
        pivot.py                    # Pivot logic between injection points
        conversation.py             # Multi-turn conversation state management
        oob.py                      # Out-of-band callback handling (reserved)
        tap.py                      # Tree of Attacks with Pruning (reserved)
        tap_roles.py                # TAP attacker/judge role definitions (reserved)
        tap_scoring.py              # TAP branch scoring heuristics (reserved)

    detectors/
        __init__.py
        hub.py                      # Detector consensus: heuristic + pattern + semantic
        base.py                     # Abstract detector base class
        judge.py                    # LLM judge detector implementation
        semantic.py                 # Semantic similarity detector

    llm/
        __init__.py
        client.py                   # Unified LLM client interface
        providers.py                # Ollama / OpenAI / Anthropic / Google adapters

    prompts/
        __init__.py
        loader.py                   # YAML prompt pack loader
        selector.py                 # Family-based depth selection by intensity
        render.py                   # Template placeholder rendering
        obfuscations.py             # Base64 / homoglyph / leet / language-switch
        schema.py                   # Prompt entry schema and validation
        packs/                      # Bundled YAML prompt packs (4 files)

    modules/
        __init__.py
        mutation.py                 # Prompt mutation strategies

    reporting/
        __init__.py
        writer.py                   # Report generation (JSON, Markdown, SARIF v2.1.0)

    utils/
        __init__.py
        logging.py                  # Thread-safe logging with ANSI colour formatting
```

## Runtime Flow

1. **Parse CLI and build config.** The CLI in `cli.py` parses arguments and constructs a `RuntimeConfig` dataclass that carries every scan setting through the pipeline.

2. **Create run workspace.** A unique `runs/<run_id>/` directory is created and a `metadata.json` file is written with scan parameters, timestamps, and target information.

3. **Load request.** The target request is loaded from either a Burp Suite XML export (`-r` flag) or a plain URL. The `*` marker in the request body, headers, or query string identifies injection locations.

4. **Fire baseline request.** A clean (uninjected) request is sent to the target. The response is stored as the diff reference for all subsequent probes.

5. **Check LLM backend connectivity.** A lightweight probe confirms that the configured LLM provider is reachable before starting the scan.

6. **Load and select prompts.** All 227 techniques are loaded from four YAML packs. The selector applies family-based depth selection controlled by the `--intensity` level, choosing N techniques per family.

7. **Pre-generate prompts.** The LLM Generator renders every selected technique into a concrete prompt string using `ThreadPoolExecutor`. Each `style_template` is populated with the user-supplied `--goal` and placeholder tokens (`{{RUN_ID}}`, `{{GOAL_PROMPT}}`, `{{CANARY_TOKEN}}`, `{{CANARY_URL}}`).

8. **Probe loop.** For each prompt and injection point combination:
   - a. Inject the prompt into a copy of the base request.
   - b. Fire the mutated request at the target and capture the response.
   - c. Diff the response body against the stored baseline.
   - d. The LLM Judge scores whether the response indicates goal achievement.
   - e. If the score exceeds the detection threshold: execute up to 5 reliability retries, requiring 3 or more confirmations (Wilson confidence interval) to promote the candidate to a confirmed finding.
   - f. If confirmed: emit the finding with prompt, technique, confidence, and evidence.

9. **Report findings.** Confirmed findings are printed in sqlmap-style output with parameter name, injection type, technique title, prompt text, and confidence score. Reports are also written to the run directory in three formats:
   - **JSON** (`report.json`) — machine-readable full scan data for automation pipelines.
   - **Markdown** (`report.md`) — human-readable report with executive summary, severity breakdown, and collapsible prompt details.
   - **SARIF v2.1.0** (`report.sarif.json`) — Static Analysis Results Interchange Format for IDE integration (VS Code SARIF Viewer, GitHub Code Scanning) and CI pipelines.

## Two LLM Roles

Both roles use the same LLM client configured by `--provider` and `--model`. Each call is stateless; no conversation history is carried between probes.

| Role          | Purpose                                                                 |
|---------------|-------------------------------------------------------------------------|
| **Generator** | Crafts a concrete prompt from a technique's `style_template` and the user-supplied `--goal`. |
| **Judge**     | Evaluates whether the target's response satisfies the goal, returning a numeric score.         |

## Prompt Packs

Four YAML packs are bundled under `llmmap/payloads/packs/`, totalling 227 techniques across 18 attack families:

| Pack | Techniques | Focus |
|------|-----------|-------|
| `pack_a_baseline.yaml`          | 14  | Direct prompt injection fundamentals (LLM01) |
| `pack_b_extended.yaml`          | 13  | Jailbreaks, role confusion, delimiter abuse |
| `pack_c_master_checklist.yaml`  | 109 | Broad OWASP LLM Top 10 coverage |
| `pack_d_full_coverage.yaml`     | 91  | Full-spectrum technique coverage |

Each entry defines: `family`, `technique`, `template`, `style_template`, `risk`, `tags`, `stage`, and `obfuscations`.

## Detection Pipeline

The `DetectorHub` aggregates multiple detection signals into a single confidence score:

- **LLM Judge** -- The primary signal. The judge detector prompts the LLM to evaluate whether the target response achieved the stated goal.
- **Pattern matching** -- Heuristic rules that look for known indicators in the response diff (e.g., canary tokens, data leakage markers).
- **Semantic similarity** -- Optional detector that measures embedding-level overlap between the response and expected goal output.

The hub computes a weighted consensus score. Candidates exceeding the `--detector-threshold` (default 0.6) proceed to reliability confirmation.

## Reliability and False-Positive Control

Every candidate finding is re-validated with `--reliability-retries` (default 5) independent probes. A finding is confirmed only when `--confirm-threshold` (default 3) of those retries also score above threshold. Confirmation statistics use the Wilson confidence interval to produce a lower-bound confidence estimate. This prevents hallucinated judge verdicts and transient server behaviour from surfacing as reported findings.

## LLM Providers

The `llmmap/llm/` package exposes a unified `LLMClient` with adapters for four backends:

| Provider    | Authentication          | Default Model              |
|-------------|-------------------------|----------------------------|
| `ollama`    | `OLLAMA_API_KEY`        | `qwen3-coder-next:cloud`   |
| `openai`    | `OPENAI_API_KEY`        | `gpt-4o-mini`              |
| `anthropic` | `ANTHROPIC_API_KEY`     | `claude-sonnet-4-20250514` |
| `google`    | `GOOGLE_API_KEY`        | `gemini-2.0-flash`         |

The default Ollama backend points at Ollama Cloud (`https://api.ollama.com`). To use local Ollama, set `OLLAMA_BASE_URL=http://127.0.0.1:11434`.

All HTTP calls -- both to LLM providers and to the scan target -- use Python's stdlib `urllib.request`. There are no third-party HTTP dependencies.

## Default Configuration

| Setting               | Default Value |
|-----------------------|---------------|
| Intensity             | 1             |
| Detection threshold   | 0.6           |
| Reliability retries   | 5             |
| Confirm threshold     | 3             |
| Max prompts          | 25            |
| Thread workers        | 1             |
| HTTP timeout          | 10 s          |
| Injection point types | Q, B, H, C, P |
| Safe mode             | On            |

## Reserved Modules

The following modules are present in the codebase but are reserved for future versions and are not active in the v1.0.0 scan pipeline:

- **TAP (Tree of Attacks with Pruning)** -- `tap.py`, `tap_roles.py`, `tap_scoring.py`. Multi-turn adaptive attack strategy where the LLM iteratively refines prompts based on prior responses. Planned for a future release.
- **OOB (Out-of-Band)** -- `oob.py`. Callback-based detection for blind injection scenarios where the target response does not directly reveal success. Planned for a future release.

---

## PromptLab

PromptLab is an interactive web-based lab built on LLMMap for learning prompt injection through sandbox simulations. It reuses LLMMap's prompt pack library and rendering engine but replaces the HTTP scan pipeline with deterministic sandbox targets and a heuristic judge.

### PromptLab Package Layout

```
promptlab/
    __init__.py
    engine/
        __init__.py
        schemas.py                  # Shared data models (SimulationResult, JudgeVerdict, etc.)
        simulator.py                # Simulation pipeline: build prompt → call target → judge
    scenarios/
        __init__.py
        registry.py                 # Scenario catalog and technique explanations
        targets.py                  # Sandbox target functions (vulnerable + defended pairs)
    api/
        __init__.py
        main.py                     # FastAPI REST API

web/                                # Next.js frontend (App Router, Tailwind CSS)
    app/
        layout.tsx
        page.tsx                    # Lab UI: landing page, scenario view, chat, explanation panel
        globals.css
```

### How PromptLab Reuses LLMMap

| LLMMap Module | PromptLab Usage |
|---------------|-----------------|
| `llmmap/prompts/loader.py` | Loads the 227 technique templates from YAML packs |
| `llmmap/prompts/selector.py` | Filters techniques by attack family for each scenario |
| `llmmap/prompts/render.py` | Renders template placeholders into concrete attack prompts |

### Simulation Flow

1. **Build attack prompt.** The simulator loads the technique's template from the LLMMap YAML packs and renders it with the scenario's goal.
2. **Call sandbox target.** The rendered prompt is passed to a Python function (not an LLM) that simulates vulnerable or defended behaviour using deterministic pattern matching.
3. **Judge the response.** A heuristic judge checks for the known secret value, disclosure signals, or refusal patterns. No LLM calls are made.
4. **Return result.** The full transcript, verdict, technique explanation, and system prompt are returned to the frontend for display.
