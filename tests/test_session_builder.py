from __future__ import annotations

from datetime import date

from src.context_models import DailyContext
from src.session_builder import SessionBuilder


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
        "time_available_min": 70,
        "location_today": "park",
        "equipment_today": ["none", "timer", "running_shoes", "resistance_band", "cones", "agility_ladder", "tennis_ball"],
        "double_session_today": False,
        "boxing_gym_session_fixed": False,
        "notes": "",
    }
    base.update(overrides)
    return DailyContext(**base)


def test_only_park_access_builds_park_compatible_session() -> None:
    builder = SessionBuilder()
    context = make_context()
    session = builder.build_session("technical_day", context)
    all_names = session.warmup + session.main_block + session.secondary_block + session.finisher + session.optional_core_mobility
    assert "bench press" not in all_names
    assert len(session.main_block) >= 1


def test_short_30_min_session_is_compact() -> None:
    builder = SessionBuilder()
    context = make_context(time_available_min=30)
    session = builder.build_session("technical_day", context)
    assert len(session.main_block) <= 2
    assert session.estimated_session_duration <= 30


def test_fight_week_reduces_volume() -> None:
    builder = SessionBuilder()
    far_context = make_context(days_to_fight=14, time_available_min=70)
    near_context = make_context(days_to_fight=7, time_available_min=70)
    far_session = builder.build_session("technical_day", far_context)
    near_session = builder.build_session("technical_day", near_context)
    assert len(near_session.main_block) <= len(far_session.main_block)
    assert len(near_session.secondary_block) <= len(far_session.secondary_block)
