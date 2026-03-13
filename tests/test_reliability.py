from __future__ import annotations

from llmmap.core.reliability import evaluate_reliability, wilson_interval


def test_wilson_interval_bounds() -> None:
    low, high = wilson_interval(3, 5)
    assert 0.0 <= low <= high <= 1.0



def test_reliability_confirmation_and_unstable_flags() -> None:
    confirmed = evaluate_reliability(success_count=3, total_runs=5, confirm_threshold=3)
    assert confirmed.confirmed is True
    assert confirmed.unstable is False

    unstable = evaluate_reliability(success_count=2, total_runs=5, confirm_threshold=3)
    assert unstable.confirmed is False
    assert unstable.unstable is True
