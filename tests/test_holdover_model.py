"""Regression checks for the paper's linear, signed holdover model."""
import pytest
from gnsdo_simulator.models.holdover import holdover_tint_seconds


@pytest.mark.parametrize("seconds", [0, -1, 3600, 86400, 30 * 86400])
@pytest.mark.parametrize("offset", [-1.8e-11, 0.0, 1.8e-11])
def test_linear_signed_accumulation_without_ageing(seconds, offset):
    entry = 12e-9
    expected = entry + offset * max(0, seconds)
    assert holdover_tint_seconds(seconds, entry, offset) == pytest.approx(
        expected, rel=1e-12, abs=1e-18)


def test_paper_threshold_and_example_values():
    assert holdover_tint_seconds(3600, 0, 1.8e-11) == pytest.approx(64.8e-9)
    assert holdover_tint_seconds(86400, 0, 1.8e-11) == pytest.approx(1.5552e-6)
    crossing = 210e-9 / 1.8e-11
    assert holdover_tint_seconds(crossing - 1, 0, 1.8e-11) < 210e-9
    assert holdover_tint_seconds(crossing + 1, 0, 1.8e-11) > 210e-9


def test_entering_holdover_preserves_phase_with_noise_enabled():
    from datetime import datetime, timedelta
    from gnsdo_simulator.device_state import (
        DeviceState, current_tint_seconds, enter_holdover)

    now = datetime(2026, 1, 1, 12)
    state = DeviceState(process_started_at=now - timedelta(seconds=400))
    before = current_tint_seconds(state, now)
    enter_holdover(state, now)
    assert current_tint_seconds(state, now) == pytest.approx(before, abs=1e-18)
