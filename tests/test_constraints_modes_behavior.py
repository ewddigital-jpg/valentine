from __future__ import annotations

from src.checkin_workflow import CheckinInput, CheckinWorkflow


def base_checkin(**overrides: object) -> CheckinInput:
    data = {
        "bodyweight_kg": 72.5,
        "sleep_hours": 7.0,
        "fatigue_1_to_5": 2,
        "soreness_1_to_5": 2,
        "energy_1_to_5": 4,
        "stress_1_to_5": 2,
        "days_to_fight": 20,
        "todays_training_plan_module": "technical_day",
        "yesterday_completion_status": "completed",
        "recent_bodyweights": [73.0, 72.9, 72.8, 72.7, 72.5],
        "fight_weight_target_kg": 70.0,
        "double_session_today": False,
        "hunger_1_to_5": 3,
        "binge_risk_note": "",
        "adherence_missed_meals": 0,
        "low_appetite_flag": False,
        "plateau_days": 0,
        "workday_limited_prep": False,
        "notes": "",
    }
    data.update(overrides)
    return CheckinInput(**data)


def test_binge_risk_enforces_structure_and_blocks_fasting() -> None:
    wf = CheckinWorkflow()
    out = wf.run(base_checkin(hunger_1_to_5=5, binge_risk_note="binge risk tonight"))
    assert any("structured meals" in rule.lower() or "minimum 3 structured meals" in rule.lower() for rule in out["enforced_rules"])
    assert "fasting" in out["blocked_actions"]
    assert "meal_skipping" in out["blocked_actions"]


def test_fight_week_blocks_aggressive_cut_actions() -> None:
    wf = CheckinWorkflow()
    out = wf.run(base_checkin(days_to_fight=6))
    assert out["mode"] == "FIGHT_WEEK"
    assert "aggressive_calorie_cut" in out["blocked_actions"]


def test_weigh_in_day_strict_intake_control() -> None:
    wf = CheckinWorkflow()
    out = wf.run(base_checkin(days_to_fight=0, notes="weigh_in_day"))
    assert out["mode"] == "WEIGH_IN_DAY"
    assert out["nutrition_module_for_day"] == "weigh_in_day_food"
    assert "experimental_foods" in out["blocked_actions"]


def test_post_weigh_in_has_phased_refeed_mode() -> None:
    wf = CheckinWorkflow()
    out = wf.run(base_checkin(days_to_fight=0, notes="post_weigh_in"))
    assert out["mode"] == "POST_WEIGH_IN_RECOVERY"
    assert out["nutrition_module_for_day"] == "post_weigh_in_refeed"


def test_high_fatigue_low_appetite_triggers_meal_simplification() -> None:
    wf = CheckinWorkflow()
    out = wf.run(base_checkin(fatigue_1_to_5=4, sleep_hours=5.9, low_appetite_flag=True))
    assert any("simplify" in item.lower() or "liquid" in item.lower() for item in out["behavior_adjustments"])


def test_plateau_with_high_stress_does_not_tighten_deficit() -> None:
    wf = CheckinWorkflow()
    out = wf.run(base_checkin(stress_1_to_5=5, plateau_days=6, recent_bodyweights=[72.5, 72.5, 72.5, 72.5, 72.5]))
    assert any("do not tighten deficit" in item.lower() for item in out["behavior_adjustments"])
