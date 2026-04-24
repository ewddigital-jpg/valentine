"""Bodyweight trend logic and conservative fight-week weight guidance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightStatus:
    trend_kg_per_week: float
    projected_weight_at_fight: float
    status_flag: str
    action_priorities: list[str]
    warnings: list[str]


def rolling_trend_kg_per_week(weights: list[float]) -> float:
    if len(weights) < 2:
        return 0.0
    start = sum(weights[: min(3, len(weights))]) / min(3, len(weights))
    end = sum(weights[-min(3, len(weights)) :]) / min(3, len(weights))
    # assumes daily check-ins
    days = max(len(weights) - 1, 1)
    return round(((end - start) / days) * 7, 3)


def evaluate_weight_trajectory(
    current_weight: float,
    fight_weight_target: float,
    days_to_fight: int,
    recent_weights: list[float],
) -> WeightStatus:
    trend = rolling_trend_kg_per_week(recent_weights)
    weeks_to_fight = max(days_to_fight / 7.0, 0.14)
    projected = round(current_weight + trend * weeks_to_fight, 2)

    needed_loss = current_weight - fight_weight_target
    projected_loss = current_weight - projected

    status = "on_track"
    warnings: list[str] = []

    if days_to_fight <= 1:
        if current_weight <= fight_weight_target + 0.3:
            status = "on_track"
        else:
            status = "clearly_behind"

    if needed_loss > 0:
        if projected_loss < needed_loss - 0.8:
            status = "clearly_behind"
        elif projected_loss < needed_loss - 0.3:
            status = "slightly_behind"

        if trend < -1.2:
            status = "too_aggressive"
            warnings.append("Weight is dropping too aggressively; reduce deficit and protect performance.")

    action_priorities = [
        "tighten food structure",
        "tighten snack control",
        "adjust carb timing",
    ]
    if status in {"clearly_behind", "slightly_behind"}:
        action_priorities.append("increase low-stress activity only if needed")

    if days_to_fight <= 7:
        warnings.append("Fight-week strategy should remain conservative; avoid aggressive dehydration.")

    return WeightStatus(
        trend_kg_per_week=trend,
        projected_weight_at_fight=projected,
        status_flag=status,
        action_priorities=action_priorities,
        warnings=warnings,
    )


def post_weigh_in_refeed_plan(bodyweight_kg: float) -> dict[str, str]:
    return {
        "phase_1": "First hour: 1-1.5 L electrolyte fluids split doses + easy carbs.",
        "phase_2": "Next 2-4 hours: repeat small carb+protein meals every 60-90 min.",
        "phase_3": f"By evening: balanced low-fiber meals; target protein across meals (~{round(bodyweight_kg*2.0)} g/day).",
        "safety": "No extreme dehydration or untested supplements.",
    }
