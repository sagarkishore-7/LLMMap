# Changelog

All notable changes to LLMMap will be documented in this file.

## v1.2.0 (2026-03-18)

### PromptLab

- **PromptLab v1** -- interactive web-based AI security lab for learning prompt injection through sandbox simulations.
  - FastAPI backend (`promptlab/`) with 5 REST endpoints.
  - Next.js frontend (`web/`) with scenario picker, attack configuration, chat visualization, mode toggle, and explanation panel.
  - Deterministic sandbox targets -- no LLM backend required.
  - Reuses all 227 LLMMap technique templates via the prompt pack library.
  - 1 scenario: Support Bot with hidden system prompt (beginner, instruction_manipulation family).
  - 6 curated technique explanations with OWASP mapping, "why it works", and mitigation guidance.
  - 32 tests (11 scenario + 12 simulator + 9 API).

### Polish

- Extracted judge heuristic signals and confidence scores to named constants in `simulator.py`.
- Pre-compiled input filter regex patterns in `targets.py` for efficiency.
- Replaced fragile `__wrapped__.__func__.__code__` introspection with direct dictionary lookup.
- Added `PROMPTLAB_CORS_ORIGINS` environment variable for CORS configuration.
- Added docstrings to `ChatMessage`, `JudgeVerdict`, and `TargetResponse`.
- Fixed `payloads/` → `prompts/` path in ARCHITECTURE.md.
- Added PromptLab section to ARCHITECTURE.md.
- Added "Why PromptLab exists", architecture diagram, and quick demo to README.
- Documented current limitations and configuration in PROMPTLAB.md.

## v1.1.0 (2026-03-18)

### Features

- **Report export** -- every scan now generates structured reports in three formats:
  - **JSON** (`report.json`) -- full scan data for automation pipelines
  - **Markdown** (`report.md`) -- human-readable report with executive summary, severity breakdown, and collapsible finding details
  - **SARIF v2.1.0** (`report.sarif.json`) -- Static Analysis Results Interchange Format for IDE integration (VS Code SARIF Viewer, GitHub Code Scanning) and CI pipelines
- **`--report-format` CLI flag** -- select output formats: `json`, `markdown`, `sarif`, or `all` (default: all). Can be specified multiple times.
- Reports are written automatically to the run directory (`runs/<run_id>/`) after scan completion, including on abort (Ctrl+C).

### Tests

- Added 17 tests for report generation covering JSON, Markdown, and SARIF output, edge cases (empty findings, severity ordering), and the format dispatcher.

## v1.0.0 (2026-03-13)

Initial public release.

### Features

- **227 prompt injection techniques** across 18 attack families, organized into 4 prompt packs: baseline, extended, master checklist, and full coverage.
- **Dual-LLM architecture** with a Generator (creates targeted prompts from goal and technique templates) and a Judge (evaluates target responses for injection success).
- **4 LLM backends** supported: Ollama (default, local), OpenAI, Anthropic, and Google.
- **Injection point discovery** across 5 location types: query parameters, body (JSON, form-encoded, multipart), headers, cookies, and path segments.
- **Burp Suite XML import** via `-r` flag for seamless integration with existing web security workflows. Direct URL targeting via `-u` flag.
- **Goal-directed prompt generation** where the generator LLM synthesizes prompts tailored to the user-specified `--goal` and each technique template.
- **Reliability confirmation** using configurable retries and Wilson confidence intervals to suppress false positives. Default: 5 retries, 3 confirmations required.
- **Obfuscation engine** with 4 methods: base64 encoding, homoglyph substitution, leet speak, and language switching.
- **sqlmap-style console output** with timestamped log levels, ANSI color coding, and `--no-color` support for CI environments.
- **Safe mode** enabled by default, blocking risky prompt families.
- **HTTP engine** with retry logic, proxy support, TLS configuration, configurable timeouts, and status code filtering.
