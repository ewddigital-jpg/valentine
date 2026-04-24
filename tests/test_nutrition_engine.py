from __future__ import annotations

from src.nutrition_engine import NutritionEngine
from src.weight_logic import evaluate_weight_trajectory


def test_normal_one_session_day_module_selection() -> None:
    engine = NutritionEngine()
    mod = engine.select_module(days_to_fight=30, selected_training_module="technical_day", double_session_today=False, notes="")
    assert mod["id"] == "technical_day_food"


def test_two_session_day_module_selection() -> None:
    engine = NutritionEngine()
    mod = engine.select_module(days_to_fight=20, selected_training_module="explosive_day", double_session_today=True, notes="")
    assert mod["id"] == "two_session_day"


def test_fight_week_selection() -> None:
    engine = NutritionEngine()
    mod = engine.select_module(days_to_fight=7, selected_training_module="technical_day", double_session_today=False, notes="")
    assert mod["id"] == "fight_week_day_food"


def test_weigh_in_day_selection() -> None:
    engine = NutritionEngine()
    mod = engine.select_module(days_to_fight=0, selected_training_module="active_recovery_day", double_session_today=False, notes="weigh_in_day")
    assert mod["id"] == "weigh_in_day_food"


def test_post_weigh_in_refeed_selection() -> None:
    engine = NutritionEngine()
    mod = engine.select_module(days_to_fight=0, selected_training_module="active_recovery_day", double_session_today=False, notes="post_weigh_in")
    assert mod["id"] == "post_weigh_in_refeed"


def test_workday_limited_prep_adds_meal_focus_flag() -> None:
    engine = NutritionEngine()
    mod = engine.select_module(days_to_fight=30, selected_training_module="technical_day", double_session_today=False, notes="")
    weight_status = evaluate_weight_trajectory(72.0, 70.0, 20, [72.3, 72.2, 72.1, 72.0])
    out = engine.daily_targets(72.0, mod, weight_status, hunger_1_to_5=2, workday_limited_prep=True, binge_risk=False)
    assert any("work-friendly" in x for x in out["meal_timing_focus"])
