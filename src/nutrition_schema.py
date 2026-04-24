"""Schema and validation for deterministic nutrition modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


REQUIRED_NUTRITION_MODULE_IDS: set[str] = {
    "rest_day",
    "one_session_day",
    "two_session_day",
    "technical_day_food",
    "explosive_day_food",
    "conditioning_day_food",
    "sparring_day_food",
    "fight_week_day_food",
    "weigh_in_day_food",
    "post_weigh_in_refeed",
    "post_fight_recovery_day_food",
}

REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "purpose",
    "protein_target_rule",
    "carb_emphasis",
    "fat_emphasis",
    "hydration_target_rule",
    "meal_timing_rules",
    "example_meals",
    "healthy_cheat_feel_meals",
    "school_work_friendly_options",
    "avoid_if",
    "notes_for_athlete",
)


class NutritionValidationError(ValueError):
    """Raised when nutrition module data is invalid."""


@dataclass(frozen=True)
class NutritionSchema:
    required_fields: tuple[str, ...] = REQUIRED_FIELDS

    def validate_module(self, module: dict[str, object]) -> None:
        missing = [field for field in self.required_fields if field not in module]
        if missing:
            raise NutritionValidationError(f"Missing fields: {missing}")

        extra = set(module) - set(self.required_fields)
        if extra:
            raise NutritionValidationError(f"Unknown fields: {sorted(extra)}")

        for field in ("id", "name", "purpose", "protein_target_rule", "carb_emphasis", "fat_emphasis", "hydration_target_rule"):
            value = module[field]
            if not isinstance(value, str) or not value.strip():
                raise NutritionValidationError(f"{field} must be non-empty string")

        for field in (
            "meal_timing_rules",
            "example_meals",
            "healthy_cheat_feel_meals",
            "school_work_friendly_options",
            "avoid_if",
            "notes_for_athlete",
        ):
            value = module[field]
            if not isinstance(value, list) or not value or not all(isinstance(x, str) and x.strip() for x in value):
                raise NutritionValidationError(f"{field} must be non-empty list of strings")

    def validate_module_list(self, modules: list[dict[str, object]]) -> None:
        if not modules:
            raise NutritionValidationError("Nutrition module list cannot be empty")
        ids: set[str] = set()
        for item in modules:
            self.validate_module(item)
            module_id = item["id"]
            if module_id in ids:
                raise NutritionValidationError(f"Duplicate nutrition module id: {module_id}")
            ids.add(module_id)  # type: ignore[arg-type]

        missing = REQUIRED_NUTRITION_MODULE_IDS - ids
        if missing:
            raise NutritionValidationError(f"Missing required nutrition module ids: {sorted(missing)}")


def load_nutrition_modules(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise NutritionValidationError("Nutrition JSON must be a list of objects")
    return data
