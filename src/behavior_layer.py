"""Behavior correction layer for adherence-risk prevention."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorResult:
    behavior_adjustments: list[str]
    rationale: list[str]


def behavior_corrections(
    hunger_1_to_5: int | None,
    fatigue_1_to_5: int,
    adherence_missed_meals: int,
    low_appetite_flag: bool,
    binge_risk: bool,
    weight_status: str,
    stress_1_to_5: int,
    plateau_days: int,
) -> BehaviorResult:
    adjustments: list[str] = []
    rationale: list[str] = []

    if binge_risk and (hunger_1_to_5 or 0) >= 4:
        adjustments.extend(
            [
                "Increase to 4 eating events today (3 meals + 1 planned snack).",
                "Use high-satiety meals (protein + potato/rice + vegetables).",
                "Remove aggressive deficit for 24h to prevent rebound binge.",
            ]
        )
        rationale.append("High hunger with binge risk requires structure-first control.")

    if low_appetite_flag and fatigue_1_to_5 >= 4:
        adjustments.extend(
            [
                "Reduce meal volume and use calorie-dense protein options.",
                "Simplify to easy-digest meals (shake + fruit + yogurt options).",
                "Prioritize liquid calories around training window.",
            ]
        )
        rationale.append("Low appetite + fatigue: simplify fueling to protect recovery.")

    if adherence_missed_meals >= 2:
        adjustments.append("Set fixed meal alarms to prevent missed feedings.")
        rationale.append("Recent missed meals increased underfueling risk.")

    if plateau_days >= 5 and stress_1_to_5 >= 4:
        adjustments.extend(
            [
                "Do not tighten deficit today.",
                "Use low-stress activity only (walk 20-30 min) if needed.",
            ]
        )
        rationale.append("Weight plateau under high stress: avoid adding stress through harder cuts.")

    if weight_status == "too_aggressive":
        adjustments.append("Add recovery-focused carbohydrate serving post-training.")
        rationale.append("Weight loss pace flagged as too aggressive; protect performance.")

    if not adjustments:
        adjustments.append("Maintain planned structure; no behavior override needed today.")
        rationale.append("No high-risk behavior pattern detected.")

    return BehaviorResult(behavior_adjustments=adjustments, rationale=rationale)
