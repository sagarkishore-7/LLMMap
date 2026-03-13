"""Week 2 scanner pipeline entrypoint."""

from __future__ import annotations

from pathlib import Path

from llmmap.config import RuntimeConfig
from llmmap.core.http_client import HttpClient, HttpExecutionOptions
from llmmap.core.models import ScanReport
from llmmap.core.orchestrator import ScanOrchestrator
from llmmap.core.request_loader import load_request


def run_scan(config: RuntimeConfig, run_dir: Path) -> ScanReport:
    """Run staged Week 2 scan pipeline and return a structured report."""
    request = load_request(config)
    client = HttpClient(
        options=HttpExecutionOptions(
            timeout_seconds=config.timeout_seconds,
            retries=config.retries,
            proxy=config.proxy,
            verify_ssl=config.verify_ssl,
        )
    )
    orchestrator = ScanOrchestrator(config=config, run_dir=run_dir, request=request, client=client)
    return orchestrator.run()
