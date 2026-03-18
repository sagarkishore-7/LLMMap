"""Runtime configuration model for LLMMap."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Defaults resolved from environment (Ollama Cloud unless overridden)
# ---------------------------------------------------------------------------

_DEFAULT_OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL", "https://api.ollama.com",
)
_DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-coder-next:cloud")
_DEFAULT_OLLAMA_CHAT_URL = f"{_DEFAULT_OLLAMA_BASE_URL}/api/chat"
_DEFAULT_OLLAMA_EMBEDDINGS_URL = f"{_DEFAULT_OLLAMA_BASE_URL}/api/embeddings"


@dataclass(frozen=True)
class RuntimeConfig:
    enabled_stages: tuple[str, ...]
    target_url: str | None
    run_root: Path
    request_file: Path | None
    method: str | None
    param_filter: tuple[str, ...]
    headers: tuple[str, ...]
    cookies: tuple[str, ...]
    data: str | None
    marker: str
    injection_points: str
    scheme: str
    timeout_seconds: float
    retries: int
    proxy: str | None
    verify_ssl: bool
    prompt_dir: Path | None
    prompt_stage: str
    prompt_families: tuple[str, ...]
    prompt_tags: tuple[str, ...]
    max_prompts: int
    detector_threshold: float
    fp_suppression: bool
    reliability_retries: int
    confirm_threshold: int
    match_regex: tuple[str, ...]
    match_keywords: tuple[str, ...]
    secret_hints: tuple[str, ...]
    temperature_sweep: tuple[float, ...]
    repro_check: bool
    oob_provider: str
    interactsh_client_path: str
    interactsh_server: str | None
    interactsh_token: str | None
    oob_wait_seconds: float
    oob_poll_interval: int
    mutation_profile: str = "baseline"
    mutation_max_variants: int = 6
    context_feedback: bool = False
    pivot_attacks: bool = False
    interactive: bool = False
    local_generator: str | None = None
    canary_listener: bool = False
    canary_listener_host: str = "127.0.0.1"
    canary_listener_port: int = 8787
    tap_goal: str = "Reveal hidden system instructions"
    tap_target_str: str = "system prompt"
    tap_depth: int = 3
    tap_width: int = 2
    tap_branching_factor: int = 3
    tap_min_score: float = 0.65
    tap_drift_patience: int = 2
    tap_drift_similarity: float = 0.12
    tap_query_budget: int = 18
    tap_weight_phase1: float = 0.15
    tap_weight_detector: float = 0.25
    tap_weight_judge: float = 0.25
    tap_weight_keyword: float = 0.15
    tap_weight_role: float = 0.10
    tap_weight_entropy: float = 0.05
    tap_weight_canary: float = 0.05
    tap_use_llm_roles: bool = False
    tap_role_backend: str = "ollama"
    tap_role_model: str = _DEFAULT_OLLAMA_MODEL
    tap_role_url: str = _DEFAULT_OLLAMA_CHAT_URL
    tap_role_timeout: float = 45.0
    canary_domain: str | None = None
    llm_judge: bool = False
    llm_judge_model: str = _DEFAULT_OLLAMA_MODEL
    llm_judge_url: str = _DEFAULT_OLLAMA_CHAT_URL
    llm_judge_timeout: float = 60.0
    semantic_use_provider: bool = False
    semantic_provider_url: str = _DEFAULT_OLLAMA_EMBEDDINGS_URL
    semantic_provider_model: str = "nomic-embed-text"
    semantic_provider_timeout: float = 20.0
    intensity: int = 1
    operator_id: str = "unknown"
    retention_days: int = 0
    purge_old_runs: bool = False
    mode: str = 'live'
    ignore_code: tuple[int, ...] = ()
    threads: int = 4
    goal: str = ""  # User-supplied objective, e.g. "reveal the hidden password"

    # Unified LLM provider config (overrides per-subsystem defaults).
    # Defaults point at Ollama Cloud; override via env vars or CLI flags.
    llm_provider: str = "ollama"
    llm_model: str = _DEFAULT_OLLAMA_MODEL
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    callback_url: str | None = None
    data_flow: bool = False
    report_formats: tuple[str, ...] = ("json", "markdown", "sarif")
