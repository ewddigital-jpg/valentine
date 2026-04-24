from __future__ import annotations

from src.compliance_tracker import ComplianceTracker
from src.load_tracker import recalculate_weekly_load, session_load
from src.state_models import WeeklyState


def test_session_load_formula() -> None:
    assert session_load(60, 7) == 42.0


def test_recalculate_weekly_load_from_completion_data() -> None:
    state = WeeklyState(week_start="2026-04-20")
    tracker = ComplianceTracker()
    tracker.mark_completed(state, "2026-04-21", "technical_day", rpe_1_to_10=6, duration_min=55)
    tracker.mark_modified(state, "2026-04-22", "explosive_day", rpe_1_to_10=8, duration_min=50)
    tracker.mark_skipped(state, "2026-04-23", "boxing_conditioning_day")

    load = recalculate_weekly_load(state)
    assert load > 0
    assert state.weekly_load_score == load
    assert len(state.rolling_fatigue_trend) >= 1
