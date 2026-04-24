"""Strict schema and validators for boxing exercise records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "category",
    "subcategory",
    "evidence_basis",
    "description",
    "primary_qualities",
    "secondary_qualities",
    "boxing_transfer_score",
    "fatigue_cost",
    "injury_risk",
    "skill_requirement",
    "equipment_needed",
    "locations",
    "suited_for",
    "avoid_if",
    "best_for_weaknesses",
    "sets_reps_guidelines",
    "intensity_guidelines",
    "rest_guidelines",
    "progression_options",
    "regression_options",
    "pair_well_with",
    "conflicts_with",
    "fight_week_ok",
    "solo_friendly",
    "notes_for_athlete",
)

VALID_CATEGORIES: set[str] = {
    "lower_body_strength",
    "lower_body_power",
    "upper_body_strength",
    "upper_body_power",
    "rotational_power",
    "boxing_specific",
    "footwork",
    "reaction",
    "trunk_stability",
    "aerobic_base",
    "conditioning_general",
    "conditioning_boxing_specific",
    "mobility",
    "recovery",
}

VALID_EVIDENCE_BASIS: set[str] = {
    "boxing_biomechanics",
    "combat_sport_strength_review",
    "combat_sport_plyometrics",
    "combat_sport_hiit_meta",
    "core_transfer_to_striking",
    "boxing_specific_conditioning",
    "aerobic_support_for_combat_sports",
    "pape_boxing",
}

LIST_FIELDS: tuple[str, ...] = (
    "evidence_basis",
    "primary_qualities",
    "secondary_qualities",
    "equipment_needed",
    "locations",
    "suited_for",
    "avoid_if",
    "best_for_weaknesses",
    "progression_options",
    "regression_options",
    "pair_well_with",
    "conflicts_with",
)

NUMERIC_1_TO_5_FIELDS: tuple[str, ...] = (
    "boxing_transfer_score",
    "fatigue_cost",
    "injury_risk",
    "skill_requirement",
)

BOOLEAN_FIELDS: tuple[str, ...] = ("fight_week_ok", "solo_friendly")


class ExerciseValidationError(ValueError):
    """Raised when an exercise violates the schema."""


@dataclass(frozen=True)
class ExerciseSchema:
    """Single-athlete boxing exercise schema helper and validator."""

    required_fields: tuple[str, ...] = REQUIRED_FIELDS

    def validate_exercise(self, exercise: dict[str, object]) -> None:
        """Validate one exercise dictionary in a strict, deterministic way."""
        missing_fields = [field for field in self.required_fields if field not in exercise]
        if missing_fields:
            raise ExerciseValidationError(f"Missing required fields: {missing_fields}")

        extra_fields = set(exercise) - set(self.required_fields)
        if extra_fields:
            raise ExerciseValidationError(f"Unknown fields are not allowed: {sorted(extra_fields)}")

        if exercise["category"] not in VALID_CATEGORIES:
            raise ExerciseValidationError(
                f"Invalid category '{exercise['category']}'."
            )

        evidence_basis = _expect_list_of_strings(exercise["evidence_basis"], "evidence_basis")
        invalid_tags = [tag for tag in evidence_basis if tag not in VALID_EVIDENCE_BASIS]
        if invalid_tags:
            raise ExerciseValidationError(
                f"Invalid evidence_basis tags: {invalid_tags}"
            )

        for field in LIST_FIELDS:
            _expect_list_of_strings(exercise[field], field)

        for field in NUMERIC_1_TO_5_FIELDS:
            value = exercise[field]
            if not isinstance(value, int) or not (1 <= value <= 5):
                raise ExerciseValidationError(f"{field} must be an integer in range 1..5")

        for field in BOOLEAN_FIELDS:
            if not isinstance(exercise[field], bool):
                raise ExerciseValidationError(f"{field} must be boolean")

        for field in ("id", "name", "subcategory", "description", "sets_reps_guidelines", "intensity_guidelines", "rest_guidelines", "notes_for_athlete"):
            value = exercise[field]
            if not isinstance(value, str) or not value.strip():
                raise ExerciseValidationError(f"{field} must be a non-empty string")

    def validate_exercise_list(self, exercises: list[dict[str, object]]) -> None:
        if not exercises:
            raise ExerciseValidationError("Exercise list must not be empty")

        ids: set[str] = set()
        names: set[str] = set()

        for exercise in exercises:
            self.validate_exercise(exercise)
            exercise_id = exercise["id"]
            exercise_name = exercise["name"]
            if exercise_id in ids:
                raise ExerciseValidationError(f"Duplicate id: {exercise_id}")
            if exercise_name in names:
                raise ExerciseValidationError(f"Duplicate name: {exercise_name}")
            ids.add(exercise_id)  # type: ignore[arg-type]
            names.add(exercise_name)  # type: ignore[arg-type]


def _expect_list_of_strings(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ExerciseValidationError(f"{field_name} must be a non-empty list of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ExerciseValidationError(f"{field_name} must contain only non-empty strings")
    return value


def load_exercises(json_path: Path) -> list[dict[str, object]]:
    """Load exercise data from JSON file."""
    with json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ExerciseValidationError("Top-level JSON value must be a list")
    if not all(isinstance(item, dict) for item in data):
        raise ExerciseValidationError("Each exercise must be a JSON object")

    return data
