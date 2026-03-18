# Roadmap

## What's in v1.0.0

LLMMap v1.0.0 ships with a complete single-stage prompt injection testing pipeline:

- **227 techniques** across 18 attack families in 4 prompt packs
- **Dual-LLM architecture** — Generator crafts goal-aware prompts; Judge scores target responses
- **4 LLM backends** — Ollama (local, default), OpenAI, Anthropic, Google
- **5 injection point classes** — query parameters, body, headers, cookies, path segments
- **Intensity levels 1-5** — controls prompts per family and obfuscation methods
- **Obfuscation engine** — base64, homoglyph, leet speak, language switch
- **Reliability confirmation** — Wilson confidence interval (5 retries, 3 confirmations)
- **Burp Suite XML import** and direct URL targeting
- **Safe mode** — blocks risky families by default

## Planned: Model Fingerprinting (Stage 0)

Automated identification of the target LLM's model family, version, and active guardrail configuration. Fingerprint results will drive prompt prioritization and technique selection — skipping techniques known to be ineffective against the detected model/guardrail combination.

## Planned: Multi-Turn Stateful Attacks (Stage 2)

Stateful conversation sequences that escalate over multiple HTTP roundtrips. Techniques include crescendo attacks, codeword priming, gradual context shifting, and other strategies that exploit conversational memory. Requires session/cookie tracking to maintain conversation state across requests.

## Planned: TAP — Tree of Attacks with Pruning (Stage 3)

Iterative LLM-driven prompt refinement where the Generator proposes prompt variations, the Judge scores them against the target, and the system follows the most promising branches while pruning dead ends. TAP enables automated discovery of novel bypasses without pre-defined technique templates.

## Planned: Out-of-Band Detection

Canary-based detection for blind prompt injection scenarios where the target does not return results directly in the HTTP response. Includes:

- Canary token generation and embedding in prompts
- DNS and HTTP callback correlation
- Integration with Interactsh and Burp Collaborator

## Planned: Indirect Prompt Injection

Injection of prompts into data sources the target LLM retrieves during processing — documents, web pages, database records, and other external inputs — rather than directly into the HTTP request.

## Planned: Multimodal Attacks

Prompt injection techniques embedded in non-text inputs: hidden text in images via OCR exploitation, QR code prompts, audio transcription injection, and other multimodal vectors that bypass text-only filtering.

## Shipped: Report Export (v1.1.0)

Structured output formats for integration with security tooling:

- **JSON** (`report.json`) — machine-readable findings for automation pipelines
- **SARIF v2.1.0** (`report.sarif.json`) — Static Analysis Results Interchange Format for IDE and CI integration
- **Markdown** (`report.md`) — human-readable reports with executive summary, severity breakdown, and finding details

Reports are generated automatically after every scan. Format selection via `--report-format` (json, markdown, sarif, all).

## Planned: Budget and Cost Tracking

Token counting and cost estimation for cloud LLM providers (OpenAI, Anthropic, Google). Configurable spend limits with abort/warn policy to prevent runaway costs during large scans.

## Planned: Plugin SDK

Extensibility framework for custom prompts, detectors, and guardrail classifiers. Stable interfaces for third-party contributions without requiring changes to the core engine.
