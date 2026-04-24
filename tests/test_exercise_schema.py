from __future__ import annotations

from pathlib import Path

import pytest

from src.exercise_schema import ExerciseSchema, ExerciseValidationError, load_exercises
from src.sample_data import get_starter_exercises


ROOT = Path(__file__).resolve().parents[1]
EXERCISES_JSON = ROOT / "src" / "exercises.json"


def test_starter_data_has_target_size() -> None:
    exercises = get_starter_exercises()
    assert 40 <= len(exercises) <= 50


def test_starter_data_includes_required_anchor_exercises() -> None:
    names = {item["name"] for item in get_starter_exercises()}
    required = {
        "back squat",
        "Bulgarian split squat",
        "countermovement jump",
        "jump squat",
        "lateral bounds",
        "box jump",
        "rotational medicine ball throw",
        "medicine ball slam",
        "landmine rotational press",
        "bench press",
        "plyometric push-up",
        "light dumbbell punch throw",
        "pull-up",
        "band resisted punches",
        "shadowboxing technical rounds",
        "shadowboxing fast flurries",
        "defensive shadow rounds",
        "ladder footwork drills",
        "cone entry exit drill",
        "reaction tennis ball catch",
        "visual cue reaction drill",
        "zone 2 run",
        "zone 2 bike",
        "sprint intervals",
        "hill sprints",
        "boxing 3x3 intervals",
        "boxing 30/30 flurry intervals",
        "plank",
        "side plank",
        "Pallof press",
        "anti-rotation walkout",
        "hip mobility flow",
        "ankle mobility series",
        "thoracic rotation flow",
        "easy shadow plus breathing reset",
    }
    assert required.issubset(names)


def test_load_exercises_requires_list_top_level(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text('{"not": "a list"}', encoding="utf-8")

    with pytest.raises(ExerciseValidationError):
        load_exercises(bad_file)


def test_schema_rejects_missing_fields() -> None:
    schema = ExerciseSchema()
    starter = get_starter_exercises()[0].copy()
    starter.pop("name")

    with pytest.raises(ExerciseValidationError):
        schema.validate_exercise(starter)


def test_schema_rejects_invalid_category() -> None:
    schema = ExerciseSchema()
    starter = get_starter_exercises()[0].copy()
    starter["category"] = "bodybuilding"

    with pytest.raises(ExerciseValidationError):
        schema.validate_exercise(starter)


def test_schema_rejects_invalid_evidence_tag() -> None:
    schema = ExerciseSchema()
    starter = get_starter_exercises()[0].copy()
    starter["evidence_basis"] = ["made_up_tag"]

    with pytest.raises(ExerciseValidationError):
        schema.validate_exercise(starter)


def test_starter_json_passes_full_validation() -> None:
    schema = ExerciseSchema()
    exercises = load_exercises(EXERCISES_JSON)
    schema.validate_exercise_list(exercises)
