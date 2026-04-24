from __future__ import annotations

from src.weight_logic import evaluate_weight_trajectory, post_weigh_in_refeed_plan


def test_bodyweight_trending_too_high_flags_behind() -> None:
    status = evaluate_weight_trajectory(
        current_weight=74.0,
        fight_weight_target=70.0,
        days_to_fight=21,
        recent_weights=[73.2, 73.4, 73.6, 73.8, 74.0],
    )
    assert status.status_flag in {"slightly_behind", "clearly_behind"}


def test_bodyweight_dropping_too_aggressive_flag() -> None:
    status = evaluate_weight_trajectory(
        current_weight=72.0,
        fight_weight_target=70.0,
        days_to_fight=20,
        recent_weights=[74.0, 73.5, 73.0, 72.4, 72.0],
    )
    assert status.status_flag == "too_aggressive"
    assert any("aggressively" in w for w in status.warnings)


def test_post_weigh_in_refeed_logic_shape() -> None:
    refeed = post_weigh_in_refeed_plan(71.0)
    assert {"phase_1", "phase_2", "phase_3", "safety"}.issubset(refeed)
