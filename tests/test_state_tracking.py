from __future__ import annotations

from datetime import date
from pathlib import Path

from src.compliance_tracker import ComplianceTracker
from src.state_models import WeeklyState
from src.state_store import StateStore
from src.weekly_planner import WeeklyContext, WeeklyPlanner


def test_state_store_persists_week(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.json")
    state = WeeklyState(week_start="2026-04-20")
    state.notes.append("persist me")
    store.save_week(state)
    loaded = store.load_week("2026-04-20")
    assert loaded is not None
    assert loaded.notes == ["persist me"]


def test_missed_explosive_session_reinsert_or_skipped_safely() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=15,
        fixed_boxing_gym_days=[],
        allow_double_sessions=False,
        prior_week_load_score=200.0,
    )
    out = planner.generate_weekly_plan(context)
    state = out["state"]

    tracker = ComplianceTracker()
    tracker.mark_skipped(state, date="2026-04-20", module_id="explosive_day", notes="work ran late")

    adjusted = planner.adjust_remaining_week(state, current_day_index=1, days_to_fight=15, high_fatigue_flag=False)
    modules = [p.module_id for p in adjusted.planned_sessions]
    assert "explosive_day" in modules or any("make-up chaos prevention" in n for n in adjusted.notes)


def test_high_fatigue_by_thursday_adjusts_remaining_week() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=12,
        fixed_boxing_gym_days=[],
        allow_double_sessions=False,
        prior_week_load_score=250.0,
    )
    out = planner.generate_weekly_plan(context)
    state = out["state"]

    adjusted = planner.adjust_remaining_week(state, current_day_index=3, days_to_fight=12, high_fatigue_flag=True)
    remaining = [p.module_id for i, p in enumerate(adjusted.planned_sessions) if i > 3]
    assert "boxing_conditioning_day" not in remaining


def test_weekly_load_spike_handling_via_adjustments() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=20,
        fixed_boxing_gym_days=[],
        allow_double_sessions=False,
        prior_week_load_score=320.0,
    )
    out = planner.generate_weekly_plan(context)
    state = out["state"]
    adjusted = planner.adjust_remaining_week(state, current_day_index=2, days_to_fight=20, high_fatigue_flag=True)
    assert any(p.module_id == "active_recovery_day" for p in adjusted.planned_sessions[3:])
