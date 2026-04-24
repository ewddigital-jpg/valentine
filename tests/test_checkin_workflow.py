from __future__ import annotations

from src.checkin_workflow import CheckinInput, CheckinWorkflow


def make_input(**overrides: object) -> CheckinInput:
    base = {
        "bodyweight_kg": 72.0,
        "sleep_hours": 7.2,
        "fatigue_1_to_5": 2,
        "soreness_1_to_5": 2,
        "energy_1_to_5": 4,
        "stress_1_to_5": 2,
        "days_to_fight": 20,
        "todays_training_plan_module": "technical_day",
        "yesterday_completion_status": "completed",
        "recent_bodyweights": [72.6, 72.4, 72.2, 72.1, 72.0],
        "fight_weight_target_kg": 70.0,
        "double_session_today": False,
        "hunger_1_to_5": 2,
        "binge_risk_note": "",
        "adherence_missed_meals": 0,
        "low_appetite_flag": False,
        "plateau_days": 0,
        "workday_limited_prep": False,
        "notes": "",
    }
    base.update(overrides)
    return CheckinInput(**base)


def test_high_fatigue_low_appetite_day() -> None:
    wf = CheckinWorkflow()
    out = wf.run(make_input(fatigue_1_to_5=4, sleep_hours=5.8, hunger_1_to_5=1))
    assert out["training_recommendation"] == "active_recovery_day"


def test_fight_in_7_days_uses_fight_week_food() -> None:
    wf = CheckinWorkflow()
    out = wf.run(make_input(days_to_fight=7))
    assert out["nutrition_module_for_day"] == "fight_week_day_food"


def test_hunger_high_binge_risk_adds_warning() -> None:
    wf = CheckinWorkflow()
    out = wf.run(make_input(hunger_1_to_5=5, binge_risk_note="binge risk after work"))
    assert any("Binge-risk" in flag or "High hunger" in flag for flag in out["warning_flags"])


def test_workday_limited_prep_mentions_work_friendly_focus() -> None:
    wf = CheckinWorkflow()
    out = wf.run(make_input(workday_limited_prep=True))
    assert any("work-friendly" in item for item in out["meal_timing_focus"])
