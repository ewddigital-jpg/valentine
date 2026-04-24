"""Strict operational modes for nutrition/weight-cut decision system."""

from __future__ import annotations

from dataclasses import dataclass


NORMAL_CUT = "NORMAL_CUT"
FIGHT_WEEK = "FIGHT_WEEK"
WEIGH_IN_DAY = "WEIGH_IN_DAY"
POST_WEIGH_IN_RECOVERY = "POST_WEIGH_IN_RECOVERY"


@dataclass(frozen=True)
class ModePolicy:
    mode: str
    module_override: str
    hydration_multiplier: float
    carb_strategy: str
    allowed_actions: list[str]
    blocked_actions: list[str]


def determine_mode(days_to_fight: int, notes: str, weight_status: str) -> str:
    notes_l = notes.lower()
    if "post_weigh_in" in notes_l:
        return POST_WEIGH_IN_RECOVERY
    if "weigh_in_day" in notes_l or days_to_fight == 0:
        return WEIGH_IN_DAY
    if days_to_fight <= 7:
        return FIGHT_WEEK
    return NORMAL_CUT


def mode_policy(mode: str) -> ModePolicy:
    if mode == POST_WEIGH_IN_RECOVERY:
        return ModePolicy(
            mode=mode,
            module_override="post_weigh_in_refeed",
            hydration_multiplier=1.2,
            carb_strategy="phased_refeed",
            allowed_actions=["phased_refeed", "electrolytes", "small_frequent_meals"],
            blocked_actions=["large_single_binge", "high_fiber_spicy_meal_early"],
        )
    if mode == WEIGH_IN_DAY:
        return ModePolicy(
            mode=mode,
            module_override="weigh_in_day_food",
            hydration_multiplier=0.9,
            carb_strategy="low_residue_control",
            allowed_actions=["small_low_residue_meals", "consistent_small_sips"],
            blocked_actions=["experimental_foods", "aggressive_dehydration"],
        )
    if mode == FIGHT_WEEK:
        return ModePolicy(
            mode=mode,
            module_override="fight_week_day_food",
            hydration_multiplier=1.0,
            carb_strategy="targeted_sharpness",
            allowed_actions=["stable_meal_schedule", "targeted_carb_timing"],
            blocked_actions=["aggressive_calorie_cut", "high_stress_extra_cardio"],
        )
    return ModePolicy(
        mode=mode,
        module_override="one_session_day",
        hydration_multiplier=1.0,
        carb_strategy="load_matched",
        allowed_actions=["structured_meals", "planned_snacks"],
        blocked_actions=["extreme_restriction", "meal_skipping_if_binge_risk"],
    )
