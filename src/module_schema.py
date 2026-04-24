"""Schema and validation for boxing training modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .exercise_schema import (
    VALID_CATEGORIES,
    load_exercises,
)


REQUIRED_MODULE_IDS: set[str] = {
    "technical_day",
    "explosive_day",
    "strength_day_lower",
    "strength_day_upper_rotation",
    "boxing_conditioning_day",
    "aerobic_base_day",
    "active_recovery_day",
    "fight_week_sharpening_day",
    "post_fight_recovery_day",
}

REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "purpose",
    "primary_goal",
    "secondary_goals",
    "suitable_when",
    "avoid_when",
    "preferred_exercise_categories",
    "preferred_primary_qualities",
    "excluded_categories",
    "excluded_exercises",
    "target_fatigue_range",
    "estimated_recovery_cost",
    "session_duration_range_min",
    "session_structure_template",
    "fight_week_ok",
    "double_session_ok",
    "notes_for_athlete",
)

VALID_PRIMARY_GOALS: set[str] = {
    "skill_quality",
    "explosive_power",
    "max_strength",
    "boxing_conditioning",
    "aerobic_base",
    "recovery",
    "fight_week_readiness",
    "post_fight_restoration",
}

VALID_RECOVERY_COSTS: set[str] = {"low", "moderate", "high"}


def _expect_non_empty_str(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModuleValidationError(f"{field} must be a non-empty string")
    return value


def _expect_list_of_strings(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ModuleValidationError(f"{field} must be a non-empty list of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ModuleValidationError(f"{field} must contain only non-empty strings")
    return value


class ModuleValidationError(ValueError):
    """Raised when module data violates schema rules."""


@dataclass(frozen=True)
class ModuleSchema:
    """Strict module schema validator for deterministic backend use."""

    required_fields: tuple[str, ...] = REQUIRED_FIELDS

    def validate_module(
        self,
        module: dict[str, object],
        valid_exercise_names: set[str],
    ) -> None:
        missing = [field for field in self.required_fields if field not in module]
        if missing:
            raise ModuleValidationError(f"Missing required fields: {missing}")

        extra = set(module) - set(self.required_fields)
        if extra:
            raise ModuleValidationError(f"Unknown fields are not allowed: {sorted(extra)}")

        _expect_non_empty_str(module["id"], "id")
        _expect_non_empty_str(module["name"], "name")
        _expect_non_empty_str(module["purpose"], "purpose")

        primary_goal = _expect_non_empty_str(module["primary_goal"], "primary_goal")
        if primary_goal not in VALID_PRIMARY_GOALS:
            raise ModuleValidationError(f"Invalid primary_goal: {primary_goal}")

        for field in (
            "secondary_goals",
            "suitable_when",
            "avoid_when",
            "preferred_exercise_categories",
            "preferred_primary_qualities",
            "excluded_categories",
            "excluded_exercises",
            "session_structure_template",
            "notes_for_athlete",
        ):
            _expect_list_of_strings(module[field], field)

        preferred_categories = _expect_list_of_strings(
            module["preferred_exercise_categories"],
            "preferred_exercise_categories",
        )
        excluded_categories = _expect_list_of_strings(
            module["excluded_categories"],
            "excluded_categories",
        )
        for category in preferred_categories + excluded_categories:
            if category not in VALID_CATEGORIES:
                raise ModuleValidationError(f"Unknown exercise category reference: {category}")

        excluded_exercises = _expect_list_of_strings(module["excluded_exercises"], "excluded_exercises")
        unknown_exercises = [name for name in excluded_exercises if name not in valid_exercise_names]
        if unknown_exercises:
            raise ModuleValidationError(f"Unknown excluded exercise references: {unknown_exercises}")

        target_fatigue_range = module["target_fatigue_range"]
        if (
            not isinstance(target_fatigue_range, list)
            or len(target_fatigue_range) != 2
            or not all(isinstance(item, int) for item in target_fatigue_range)
        ):
            raise ModuleValidationError("target_fatigue_range must be [min, max] ints")
        min_fatigue, max_fatigue = target_fatigue_range
        if not (1 <= min_fatigue <= max_fatigue <= 5):
            raise ModuleValidationError("target_fatigue_range values must be in 1..5 and ordered")

        recovery_cost = _expect_non_empty_str(module["estimated_recovery_cost"], "estimated_recovery_cost")
        if recovery_cost not in VALID_RECOVERY_COSTS:
            raise ModuleValidationError("estimated_recovery_cost must be one of: low, moderate, high")

        duration_range = module["session_duration_range_min"]
        if (
            not isinstance(duration_range, list)
            or len(duration_range) != 2
            or not all(isinstance(item, int) for item in duration_range)
        ):
            raise ModuleValidationError("session_duration_range_min must be [min, max] ints")
        min_duration, max_duration = duration_range
        if not (20 <= min_duration <= max_duration <= 180):
            raise ModuleValidationError("session_duration_range_min values must be practical and ordered")

        for flag in ("fight_week_ok", "double_session_ok"):
            if not isinstance(module[flag], bool):
                raise ModuleValidationError(f"{flag} must be boolean")

    def validate_module_list(
        self,
        modules: list[dict[str, object]],
        valid_exercise_names: set[str],
    ) -> None:
        if not modules:
            raise ModuleValidationError("Module list must not be empty")

        ids: set[str] = set()
        for module in modules:
            self.validate_module(module, valid_exercise_names)
            module_id = module["id"]
            if module_id in ids:
                raise ModuleValidationError(f"Duplicate module id: {module_id}")
            ids.add(module_id)  # type: ignore[arg-type]

        missing_ids = REQUIRED_MODULE_IDS - ids
        if missing_ids:
            raise ModuleValidationError(f"Missing required module ids: {sorted(missing_ids)}")


def load_modules(json_path: Path) -> list[dict[str, object]]:
    with json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ModuleValidationError("Top-level JSON value must be a list")
    if not all(isinstance(item, dict) for item in data):
        raise ModuleValidationError("Each module must be a JSON object")
    return data


def build_valid_exercise_name_set(exercises_path: Path) -> set[str]:
    exercises = load_exercises(exercises_path)
    return {item["name"] for item in exercises if isinstance(item.get("name"), str)}
