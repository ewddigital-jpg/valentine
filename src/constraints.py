"""Hard constraints that override nutrition decisions under risk conditions."""

from __future__ import annotations

from dataclasses import dataclass

from .modes import FIGHT_WEEK, WEIGH_IN_DAY


MAX_WEIGHT_LOSS_RATE_KG_PER_WEEK = 1.0
MIN_PROTEIN_G_PER_KG = 1.8
MIN_HYDRATION_ML_PER_KG = 35
ANTI_BINGE_MIN_MEALS = 3
MAX_DEHYDRATION_RISK_FLAG = "no_aggressive_dehydration"


@dataclass(frozen=True)
class ConstraintResult:
    enforced_rules: list[str]
    blocked_actions: list[str]
    nutrition_module_override: str | None
    protein_floor_g: int | None
    hydration_floor_ml: int | None
    forced_meal_timing: list[str]


def apply_hard_constraints(
    bodyweight_kg: float,
    mode: str,
    weight_status: str,
    hunger_1_to_5: int | None,
    binge_risk: bool,
    days_to_fight: int,
) -> ConstraintResult:
    enforced: list[str] = []
    blocked: list[str] = []
    override_module: str | None = None
    forced_meal_timing: list[str] = []

    protein_floor = int(round(bodyweight_kg * MIN_PROTEIN_G_PER_KG))
    hydration_floor = int(round(bodyweight_kg * MIN_HYDRATION_ML_PER_KG))

    enforced.append(f"Protein must be >= {protein_floor} g today.")
    enforced.append(f"Hydration must be >= {hydration_floor} ml today.")

    if weight_status == "too_aggressive":
        enforced.append("Deficit reduction is mandatory today to protect performance and health.")
        blocked.append("additional_calorie_cut")
        override_module = "one_session_day"

    if binge_risk and (hunger_1_to_5 or 0) >= 4:
        enforced.append(f"Minimum {ANTI_BINGE_MIN_MEALS} structured meals required; no skipping.")
        forced_meal_timing.extend(
            [
                "Mandatory breakfast protein feeding.",
                "Planned afternoon anti-binge snack.",
                "Pre-logged dinner with dessert substitute.",
            ]
        )
        blocked.extend(["fasting", "meal_skipping", "unplanned_takeaway_binge"])

    if mode == FIGHT_WEEK:
        enforced.append("Fight-week rule: keep hydration and sodium stable, no aggressive cutting.")
        blocked.extend(["aggressive_dehydration", "extra_high_stress_cardio"])

    if mode == WEIGH_IN_DAY or days_to_fight == 0:
        enforced.append("Weigh-in day: only low-residue familiar foods in controlled portions.")
        blocked.extend(["experimental_foods", "high_fiber_bulky_meals", "extreme_dehydration_methods"])

    enforced.append(f"Hydration safety constraint active: {MAX_DEHYDRATION_RISK_FLAG}.")

    return ConstraintResult(
        enforced_rules=_dedupe(enforced),
        blocked_actions=_dedupe(blocked),
        nutrition_module_override=override_module,
        protein_floor_g=protein_floor,
        hydration_floor_ml=hydration_floor,
        forced_meal_timing=forced_meal_timing,
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out
