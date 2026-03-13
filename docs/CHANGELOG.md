# Changelog

All notable changes to LLMMap will be documented in this file.

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
