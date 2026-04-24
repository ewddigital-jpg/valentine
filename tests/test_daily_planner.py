from __future__ import annotations

from datetime import date

from src.context_models import DailyContext
from src.daily_planner import DailyPlanner


def make_context(**overrides: object) -> DailyContext:
    base = {
        "date": date(2026, 4, 22),
        "bodyweight_kg": 72.0,
        "sleep_hours": 7.6,
        "fatigue_1_to_5": 2,
        "soreness_upper_1_to_5": 2,
        "soreness_lower_1_to_5": 2,
        "energy_1_to_5": 4,
        "stress_1_to_5": 2,
        "motivation_1_to_5": 4,
        "days_to_fight": 14,
        "last_session_module": "technical_day",
        "last_session_intensity": 3,
        "yesterday_had_run": False,
        "yesterday_had_sprints": False,
        "yesterday_had_sparring": False,
        "weekly_load_score": 15,
        "time_available_min": 80,
        "location_today": "gym",
        "equipment_today": [
            "none", "barbell", "rack", "dumbbells", "bench", "medicine_ball", "wall", "landmine", "resistance_band", "timer", "bike", "running_shoes", "pullup_bar", "cones", "agility_ladder", "tennis_ball"
        ],
        "double_session_today": True,
        "boxing_gym_session_fixed": False,
        "notes": "",
    }
    base.update(overrides)
    return DailyContext(**base)


def test_daily_plan_output_shape_and_optional_second_session() -> None:
    planner = DailyPlanner()
    context = make_context()
    plan = planner.build_daily_plan(context)
    assert {"selected_module", "module_rationale", "readiness_summary", "session_1", "session_2_optional", "warnings", "recovery_notes"}.issubset(plan)
    assert plan["session_2_optional"] is not None


def test_lower_body_soreness_high_prefers_non_lower_body_module() -> None:
    planner = DailyPlanner()
    context = make_context(soreness_lower_1_to_5=5, fatigue_1_to_5=3)
    plan = planner.build_daily_plan(context)
    assert plan["selected_module"] not in {"strength_day_lower", "explosive_day", "boxing_conditioning_day"}


def test_days_to_fight_7_prefers_sharpening_or_technical() -> None:
    planner = DailyPlanner()
    context = make_context(days_to_fight=7)
    plan = planner.build_daily_plan(context)
    assert plan["selected_module"] in {"fight_week_sharpening_day", "technical_day", "active_recovery_day"}
