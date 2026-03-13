"""Reliability checks and reproducibility metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ReliabilityResult:
    total_runs: int
    success_count: int
    confirm_threshold: int
    confirmed: bool
    p_hat: float
    ci_low: float
    ci_high: float
    unstable: bool



def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson confidence interval for Bernoulli success ratio."""
    if total <= 0:
        return (0.0, 0.0)

    phat = successes / total
    denom = 1.0 + (z * z) / total
    center = (phat + (z * z) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * total)) / total)
    return (max(0.0, center - margin), min(1.0, center + margin))



def evaluate_reliability(
    success_count: int,
    total_runs: int,
    confirm_threshold: int,
) -> ReliabilityResult:
    """Evaluate confirmation and reproducibility status."""
    p_hat = (success_count / total_runs) if total_runs > 0 else 0.0
    ci_low, ci_high = wilson_interval(success_count, total_runs)
    confirmed = success_count >= max(1, confirm_threshold)
    unstable = (success_count > 0) and not confirmed

    return ReliabilityResult(
        total_runs=total_runs,
        success_count=success_count,
        confirm_threshold=confirm_threshold,
        confirmed=confirmed,
        p_hat=p_hat,
        ci_low=ci_low,
        ci_high=ci_high,
        unstable=unstable,
    )
