from __future__ import annotations

from datetime import date

from src.weekly_planner import WeeklyContext, WeeklyPlanner


def test_normal_non_fight_week_plan_has_distribution() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=20,
        fixed_boxing_gym_days=[],
        allow_double_sessions=True,
        prior_week_load_score=210.0,
    )
    out = planner.generate_weekly_plan(context)
    modules = [d["module_id"] for d in out["day_by_day_module_plan"]]
    assert "technical_day" in modules
    assert "aerobic_base_day" in modules or "active_recovery_day" in modules


def test_fight_in_10_days_limits_high_fatigue() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=10,
        fixed_boxing_gym_days=[],
        allow_double_sessions=False,
        prior_week_load_score=220.0,
    )
    out = planner.generate_weekly_plan(context)
    high = [d for d in out["day_by_day_module_plan"] if d["module_id"] in {"strength_day_lower", "boxing_conditioning_day"}]
    assert len(high) <= 2


def test_fight_in_5_days_sharpening_bias() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=5,
        fixed_boxing_gym_days=[],
        allow_double_sessions=False,
        prior_week_load_score=180.0,
    )
    out = planner.generate_weekly_plan(context)
    modules = [d["module_id"] for d in out["day_by_day_module_plan"]]
    assert "fight_week_sharpening_day" in modules
    assert "strength_day_lower" not in modules


def test_fixed_boxing_gym_sessions_are_anchored() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=18,
        fixed_boxing_gym_days=[1, 4],
        allow_double_sessions=False,
        prior_week_load_score=200.0,
    )
    out = planner.generate_weekly_plan(context)
    day1 = out["day_by_day_module_plan"][1]
    day4 = out["day_by_day_module_plan"][4]
    assert day1["module_id"] in {"technical_day", "fight_week_sharpening_day"}
    assert day4["module_id"] in {"technical_day", "fight_week_sharpening_day"}


def test_sunday_auto_rest() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=25,
        fixed_boxing_gym_days=[],
        allow_double_sessions=True,
        prior_week_load_score=160.0,
    )
    out = planner.generate_weekly_plan(context)
    sunday = out["day_by_day_module_plan"][6]
    assert sunday["module_id"] == "active_recovery_day"


def test_double_session_overuse_prevention() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=25,
        fixed_boxing_gym_days=[],
        allow_double_sessions=True,
        prior_week_load_score=160.0,
    )
    out = planner.generate_weekly_plan(context)
    doubles = [d for d in out["day_by_day_module_plan"] if d["double_session"]]
    assert len(doubles) <= 5
    assert all(d["module_id"] != "active_recovery_day" for d in doubles)


def test_lower_body_soreness_changes_lower_loading() -> None:
    planner = WeeklyPlanner()
    context = WeeklyContext(
        week_start=date(2026, 4, 20),
        days_to_fight=16,
        fixed_boxing_gym_days=[],
        allow_double_sessions=False,
        prior_week_load_score=160.0,
        lower_body_soreness_1_to_5=4,
    )
    out = planner.generate_weekly_plan(context)
    modules = [d["module_id"] for d in out["day_by_day_module_plan"]]
    assert "strength_day_lower" not in modules
