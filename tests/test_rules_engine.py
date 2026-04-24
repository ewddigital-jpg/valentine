from __future__ import annotations

from datetime import date

from src.context_models import DailyContext
from src.rules_engine import RulesEngine


def make_context(**overrides: object) -> DailyContext:
    base = {
        "date": date(2026, 4, 22),
        "bodyweight_kg": 72.0,
        "sleep_hours": 7.8,
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
        "weekly_load_score": 16,
        "time_available_min": 70,
        "location_today": "gym",
        "equipment_today": [
            "none",
            "barbell",
            "rack",
            "dumbbells",
            "bench",
            "medicine_ball",
            "wall",
            "landmine",
            "resistance_band",
            "timer",
            "bike",
            "running_shoes",
            "pullup_bar",
            "cones",
            "agility_ladder",
        ],
        "double_session_today": False,
        "boxing_gym_session_fixed": False,
        "notes": "",
    }
    base.update(overrides)
    return DailyContext(**base)


def test_fresh_athlete_prefers_explosive_or_strength() -> None:
    engine = RulesEngine()
    context = make_context()
    decision = engine.select_modules(context)
    assert decision.primary_module_id in {"explosive_day", "strength_day_lower", "strength_day_upper_rotation"}


def test_high_fatigue_poor_sleep_prefers_recovery_or_technical() -> None:
    engine = RulesEngine()
    context = make_context(fatigue_1_to_5=4, sleep_hours=5.8, energy_1_to_5=2)
    decision = engine.select_modules(context)
    assert decision.primary_module_id in {"active_recovery_day", "technical_day"}


def test_day_after_run_deprioritizes_aerobic_module() -> None:
    engine = RulesEngine()
    context = make_context(yesterday_had_run=True)
    decision = engine.select_modules(context)
    assert decision.primary_module_id != "aerobic_base_day"


def test_day_after_sparring_with_sore_legs_avoids_heavy_lower() -> None:
    engine = RulesEngine()
    context = make_context(yesterday_had_sparring=True, soreness_lower_1_to_5=4, fatigue_1_to_5=3)
    decision = engine.select_modules(context)
    assert decision.primary_module_id not in {"strength_day_lower", "boxing_conditioning_day", "explosive_day"}


def test_fight_in_two_days_avoids_heavy_modules() -> None:
    engine = RulesEngine()
    context = make_context(days_to_fight=2)
    decision = engine.select_modules(context)
    assert decision.primary_module_id not in {"strength_day_lower", "boxing_conditioning_day"}


def test_sunday_defaults_to_light_recovery() -> None:
    engine = RulesEngine()
    context = make_context(date=date(2026, 4, 26))
    decision = engine.select_modules(context)
    assert decision.primary_module_id == "active_recovery_day"
