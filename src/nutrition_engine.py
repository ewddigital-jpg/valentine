"""Deterministic nutrition module selection and target generation."""

from __future__ import annotations

from pathlib import Path

from .nutrition_schema import NutritionSchema, load_nutrition_modules
from .weight_logic import WeightStatus


ROOT = Path(__file__).resolve().parents[1]
MODULES_PATH = ROOT / "src" / "nutrition_modules.json"


class NutritionEngine:
    def __init__(self) -> None:
        modules = load_nutrition_modules(MODULES_PATH)
        NutritionSchema().validate_module_list(modules)
        self.modules = {item["id"]: item for item in modules}

    def select_module(
        self,
        days_to_fight: int,
        selected_training_module: str,
        double_session_today: bool,
        notes: str,
    ) -> dict[str, object]:
        notes_l = notes.lower()
        if "post_weigh_in" in notes_l:
            return self.modules["post_weigh_in_refeed"]
        if "weigh_in_day" in notes_l or days_to_fight == 0:
            return self.modules["weigh_in_day_food"]
        if "post_fight" in notes_l:
            return self.modules["post_fight_recovery_day_food"]
        if days_to_fight <= 7:
            return self.modules["fight_week_day_food"]
        if double_session_today:
            return self.modules["two_session_day"]
        if selected_training_module in {"active_recovery_day", "post_fight_recovery_day"}:
            return self.modules["rest_day"]
        if selected_training_module == "technical_day":
            return self.modules["technical_day_food"]
        if selected_training_module == "explosive_day":
            return self.modules["explosive_day_food"]
        if selected_training_module in {"boxing_conditioning_day", "aerobic_base_day"}:
            return self.modules["conditioning_day_food"]
        if selected_training_module == "sparring_day":
            return self.modules["sparring_day_food"]
        return self.modules["one_session_day"]

    def daily_targets(
        self,
        bodyweight_kg: float,
        module: dict[str, object],
        weight_status: WeightStatus,
        hunger_1_to_5: int | None,
        workday_limited_prep: bool,
        binge_risk: bool,
    ) -> dict[str, object]:
        protein_g = round(bodyweight_kg * (2.2 if "2.2" in str(module["protein_target_rule"]) else 2.0))
        hydration_ml = int(bodyweight_kg * (45 if "50" in str(module["hydration_target_rule"]) or "45" in str(module["hydration_target_rule"]) else 40))

        warning_flags: list[str] = []
        if weight_status.status_flag == "too_aggressive":
            warning_flags.append("Weight loss pace too aggressive. Pull back deficit.")
        if binge_risk:
            warning_flags.append("Binge-risk note present: pre-plan meals and lock snack boundaries.")
        if hunger_1_to_5 is not None and hunger_1_to_5 >= 4:
            warning_flags.append("High hunger: prioritize high-volume protein meals and planned dessert option.")

        meal_focus = list(module["meal_timing_rules"])
        if workday_limited_prep:
            meal_focus.append("Use work-friendly pre-packed options only; remove decision friction.")

        return {
            "nutrition_module_id": module["id"],
            "protein_target_g": protein_g,
            "hydration_target_ml": hydration_ml,
            "meal_timing_focus": meal_focus,
            "example_meals": module["example_meals"],
            "healthy_cheat_feel_meals": module["healthy_cheat_feel_meals"],
            "school_work_friendly_options": module["school_work_friendly_options"],
            "weight_action_priorities": weight_status.action_priorities,
            "warning_flags": warning_flags + weight_status.warnings,
        }
