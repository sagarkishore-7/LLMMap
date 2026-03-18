# LLMMap

![LLMMap](assets/screenshot.png)

**LLMMap** is an automated prompt injection testing framework for LLM-integrated applications. It discovers injection points in HTTP requests, generates targeted attack prompts using a dual-LLM architecture, fires them at the target, and confirms findings with statistical reliability testing. Inspired by [sqlmap](https://sqlmap.org/), LLMMap brings the same systematic, evidence-backed approach to LLM security testing.

> **Legal disclaimer:** Usage of LLMMap for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. The developers assume no liability and are not responsible for any misuse or damage caused by this program.

---

## PromptLab — Interactive AI Security Lab

**PromptLab** is a web-based lab built on LLMMap for learning prompt injection and LLM defense strategies through hands-on sandbox simulations. No API keys required.

### Why PromptLab exists

Most developers learn about prompt injection from blog posts and slides. PromptLab lets you **see an attack succeed, then toggle to a defended version and understand exactly why the defense works** — all inside a safe sandbox that never contacts external systems. The goal is to make LLM security intuitive enough that every team building on LLMs can ship with defenses from day one.

### Architecture

```
┌─────────────────┐     HTTP/JSON     ┌──────────────────────┐
│   Next.js UI    │ ◄──────────────►  │   FastAPI API         │
│   (web/)        │                    │   (promptlab/api/)    │
└─────────────────┘                    └──────────┬───────────┘
                                                  │
                                       ┌──────────┴──────────┐
                                       │  Simulation Engine   │
                                       │  (promptlab/engine/) │
                                       └──────────┬──────────┘
                                                  │
                              ┌────────────────────┼──────────────────┐
                              │                    │                  │
                     ┌────────┴──────┐   ┌────────┴──────┐  ┌───────┴──────┐
                     │   Sandbox     │   │   LLMMap      │  │  Deterministic│
                     │   Targets     │   │   Prompt      │  │  Judge        │
                     │  (scenarios/) │   │   Packs (227) │  │               │
                     └───────────────┘   └───────────────┘  └──────────────┘
```

- **Sandbox targets** are Python functions — no LLM backend needed for demos.
- **Prompt packs** are reused directly from the LLMMap technique library.
- **Deterministic judge** uses known secrets + heuristic signals; no LLM calls.

### Quick Demo

```bash
# 1. Install (from project root)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[web]"

# 2. Start the API (no LLM backend needed — sandbox is deterministic)
uvicorn promptlab.api.main:app --reload --port 8000

# 3. Start the frontend (separate terminal)
cd web && npm install && npm run dev

# 4. Open http://localhost:3000
```

For production deployment (Railway + Vercel), see [Deployment Guide](docs/DEPLOYMENT.md).

Or test the API directly:

```bash
# List scenarios
curl http://localhost:8000/api/scenarios

# Run a vulnerable simulation
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"support_bot","technique_id":"rule_addition_prompting","mode":"vulnerable"}'

# Run the same attack against the defended version
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"support_bot","technique_id":"rule_addition_prompting","mode":"defended"}'
```

See [PromptLab documentation](docs/PROMPTLAB.md) for full details.

---

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Requirements: Python >= 3.11. Only dependency: PyYAML.

## Usage

LLMMap accepts targets via Burp Suite request export (`-r`) or URL (`-u`). Place `*` where the prompt should be injected.

```bash
# Default: Ollama Cloud (set OLLAMA_API_KEY)
export OLLAMA_API_KEY=your-key
llmmap -u "https://target.example.com/chat?q=*" --goal "reveal the hidden password"

# Burp Suite request capture
llmmap -r request --goal "reveal the system prompt"

# Alternative providers (OpenAI, Anthropic, Google)
export OPENAI_API_KEY=sk-...
llmmap -r request --goal "reveal the system prompt" --provider openai

# Local Ollama (advanced)
export OLLAMA_BASE_URL=http://127.0.0.1:11434
llmmap -r request --goal "reveal the system prompt"

# Intensity control (1-5, default: 1)
llmmap -r request --goal "reveal the system prompt" --intensity 3

# Limit to specific parameters or injection point classes
llmmap -r request --goal "..." -p prompt --injection-points QB
```

### Report Export

Every scan automatically generates reports in JSON, Markdown, and SARIF format in the run directory. Control output formats with `--report-format`:

```bash
# All formats (default)
llmmap -r request --goal "reveal the system prompt"

# JSON only (for CI pipelines)
llmmap -r request --goal "reveal the system prompt" --report-format json

# Multiple specific formats
llmmap -r request --goal "reveal the system prompt" --report-format json --report-format sarif
```

Reports are written to `runs/<run_id>/`:
- `report.json` -- machine-readable full scan data
- `report.md` -- human-readable summary with finding details
- `report.sarif.json` -- SARIF v2.1.0 for IDE and CI integration (GitHub Code Scanning, VS Code SARIF Viewer, etc.)

Full option reference:

```
llmmap -h
```

## Features

- **227 prompt injection techniques** across 18 attack families, organized in 4 prompt packs
- **Dual-LLM architecture** -- Generator crafts goal-aware prompts; Judge evaluates target responses
- **4 LLM backends** -- Ollama (default, local, no API key), OpenAI, Anthropic, Google
- **5 injection point classes** -- query parameters (Q), body (B), headers (H), cookies (C), path (P)
- **Intensity levels 1-5** -- controls prompts per family (1/2/4/8/16) and obfuscation methods
- **Obfuscation engine** -- base64, homoglyph, leet speak, language switch
- **Statistical confirmation** -- Wilson confidence interval with configurable retries (default: 5 retries, 3 successes)
- **Safe mode** -- enabled by default; blocks risky prompt families
- **Burp Suite integration** -- reads request exports natively; proxy support for traffic inspection
- **sqlmap-style output** -- timestamped, color-coded console logging with `--no-color` support
- **Dry-run mode** -- validate scan configuration without sending requests
- **Report export** -- JSON, Markdown, and SARIF output for CI/CD integration and documentation
- **PromptLab** -- interactive web lab for learning prompt injection through sandbox simulations

## LLMMap Architecture

```
Target (-r/-u)
    |
    v
Injection Point Discovery (Q/B/H/C/P)
    |
    v
Prompt Generation (Generator LLM + technique library)
    |
    v
Request Mutation & Delivery
    |
    v
Response Analysis (Judge LLM + heuristic detectors)
    |
    v
Reliability Confirmation (Wilson CI)
    |
    v
Findings Report
```

Default backend: [Ollama Cloud](https://ollama.com) (set `OLLAMA_API_KEY`). Also supports: OpenAI, Anthropic, Google. For local Ollama, set `OLLAMA_BASE_URL=http://127.0.0.1:11434`.

## Links

- [Architecture](docs/ARCHITECTURE.md)
- [PromptLab](docs/PROMPTLAB.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Authorization and safety](docs/AUTHORIZATION.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)
- [Roadmap](docs/TODO.md)
- [License](LICENSE)
