"""Daily check-in workflow combining training, weight, and nutrition guidance."""

from __future__ import annotations

from dataclasses import dataclass

from .behavior_layer import behavior_corrections
from .constraints import apply_hard_constraints
from .modes import mode_policy, determine_mode
from .nutrition_engine import NutritionEngine
from .weight_logic import evaluate_weight_trajectory


@dataclass(frozen=True)
class CheckinInput:
    bodyweight_kg: float
    sleep_hours: float
    fatigue_1_to_5: int
    soreness_1_to_5: int
    energy_1_to_5: int
    stress_1_to_5: int
    days_to_fight: int
    todays_training_plan_module: str
    yesterday_completion_status: str
    recent_bodyweights: list[float]
    fight_weight_target_kg: float
    double_session_today: bool = False
    hunger_1_to_5: int | None = None
    binge_risk_note: str = ""
    adherence_missed_meals: int = 0
    low_appetite_flag: bool = False
    plateau_days: int = 0
    workday_limited_prep: bool = False
    notes: str = ""


class CheckinWorkflow:
    def __init__(self) -> None:
        self.nutrition = NutritionEngine()

    def run(self, checkin: CheckinInput) -> dict[str, object]:
        weight_status = evaluate_weight_trajectory(
            current_weight=checkin.bodyweight_kg,
            fight_weight_target=checkin.fight_weight_target_kg,
            days_to_fight=checkin.days_to_fight,
            recent_weights=checkin.recent_bodyweights,
        )

        training_recommendation = self._training_recommendation(checkin)
        mode = determine_mode(
            days_to_fight=checkin.days_to_fight,
            notes=f"{checkin.notes} {checkin.binge_risk_note}",
            weight_status=weight_status.status_flag,
        )
        policy = mode_policy(mode)
        mode_module_id = policy.module_override

        selected_module = self.nutrition.modules.get(mode_module_id) or self.nutrition.select_module(
            days_to_fight=checkin.days_to_fight,
            selected_training_module=training_recommendation,
            double_session_today=checkin.double_session_today,
            notes=f"{checkin.notes} {checkin.binge_risk_note}",
        )

        constraint_result = apply_hard_constraints(
            bodyweight_kg=checkin.bodyweight_kg,
            mode=mode,
            weight_status=weight_status.status_flag,
            hunger_1_to_5=checkin.hunger_1_to_5,
            binge_risk="binge" in checkin.binge_risk_note.lower(),
            days_to_fight=checkin.days_to_fight,
        )

        if constraint_result.nutrition_module_override is not None:
            selected_module = self.nutrition.modules[constraint_result.nutrition_module_override]

        behavior_result = behavior_corrections(
            hunger_1_to_5=checkin.hunger_1_to_5,
            fatigue_1_to_5=checkin.fatigue_1_to_5,
            adherence_missed_meals=checkin.adherence_missed_meals,
            low_appetite_flag=checkin.low_appetite_flag,
            binge_risk="binge" in checkin.binge_risk_note.lower(),
            weight_status=weight_status.status_flag,
            stress_1_to_5=checkin.stress_1_to_5,
            plateau_days=checkin.plateau_days,
        )

        nutrition_targets = self.nutrition.daily_targets(
            bodyweight_kg=checkin.bodyweight_kg,
            module=selected_module,
            weight_status=weight_status,
            hunger_1_to_5=checkin.hunger_1_to_5,
            workday_limited_prep=checkin.workday_limited_prep,
            binge_risk="binge" in checkin.binge_risk_note.lower(),
        )

        if constraint_result.protein_floor_g is not None:
            nutrition_targets["protein_target_g"] = max(
                nutrition_targets["protein_target_g"], constraint_result.protein_floor_g
            )
        if constraint_result.hydration_floor_ml is not None:
            nutrition_targets["hydration_target_ml"] = max(
                nutrition_targets["hydration_target_ml"], constraint_result.hydration_floor_ml
            )

        nutrition_targets["hydration_target_ml"] = int(
            nutrition_targets["hydration_target_ml"] * policy.hydration_multiplier
        )
        nutrition_targets["meal_timing_focus"] = (
            constraint_result.forced_meal_timing + nutrition_targets["meal_timing_focus"]
        )

        rationale = [
            f"Mode selected first: {mode}.",
            f"Training module considered: {training_recommendation}.",
            f"Weight status: {weight_status.status_flag} at trend {weight_status.trend_kg_per_week} kg/week.",
            f"Nutrition module selected: {selected_module['id']}.",
            *behavior_result.rationale,
        ]

        warning_flags = list(nutrition_targets["warning_flags"]) + constraint_result.blocked_actions
        if checkin.sleep_hours < 6.5 and checkin.fatigue_1_to_5 >= 4:
            warning_flags.append("Recovery risk: low sleep + high fatigue.")

        blocked_actions = _dedupe(constraint_result.blocked_actions + policy.blocked_actions)

        return {
            "training_recommendation": training_recommendation,
            "mode": mode,
            "enforced_rules": constraint_result.enforced_rules,
            "blocked_actions": blocked_actions,
            "behavior_adjustments": behavior_result.behavior_adjustments,
            "nutrition_module_for_day": selected_module["id"],
            "protein_target": nutrition_targets["protein_target_g"],
            "hydration_target": nutrition_targets["hydration_target_ml"],
            "meal_timing_focus": nutrition_targets["meal_timing_focus"],
            "warning_flags": warning_flags,
            "rationale": rationale,
            "weight_status": weight_status.status_flag,
            "weight_actions": weight_status.action_priorities,
            "example_meals": nutrition_targets["example_meals"],
            "healthy_cheat_feel_meals": nutrition_targets["healthy_cheat_feel_meals"],
            "school_work_friendly_options": nutrition_targets["school_work_friendly_options"],
            "active_intervention": None,
        }

    def _training_recommendation(self, checkin: CheckinInput) -> str:
        if checkin.days_to_fight <= 2:
            return "fight_week_sharpening_day"
        if checkin.fatigue_1_to_5 >= 4 and checkin.sleep_hours < 6.5:
            return "active_recovery_day"
        if checkin.soreness_1_to_5 >= 4:
            return "technical_day"
        if checkin.yesterday_completion_status == "skipped" and checkin.energy_1_to_5 >= 3:
            return checkin.todays_training_plan_module
        return checkin.todays_training_plan_module


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out
