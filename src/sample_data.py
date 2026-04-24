"""Helpers for loading and validating the starter exercise database."""

from __future__ import annotations

from pathlib import Path

from .exercise_schema import ExerciseSchema, load_exercises


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_EXERCISES_PATH = ROOT_DIR / "src" / "exercises.json"


def get_starter_exercises() -> list[dict[str, object]]:
    """Load and validate the starter exercise database."""
    schema = ExerciseSchema()
    exercises = load_exercises(DEFAULT_EXERCISES_PATH)
    schema.validate_exercise_list(exercises)
    return exercises


if __name__ == "__main__":
    loaded = get_starter_exercises()
    print(f"Loaded and validated {len(loaded)} exercises from {DEFAULT_EXERCISES_PATH}")
