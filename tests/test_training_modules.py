from __future__ import annotations

from pathlib import Path

import pytest

from src.module_loader import get_training_modules
from src.module_schema import (
    ModuleSchema,
    ModuleValidationError,
    REQUIRED_MODULE_IDS,
    build_valid_exercise_name_set,
    load_modules,
)


ROOT = Path(__file__).resolve().parents[1]
MODULES_JSON = ROOT / "src" / "training_modules.json"
EXERCISES_JSON = ROOT / "src" / "exercises.json"


def test_required_modules_present() -> None:
    modules = get_training_modules()
    ids = {module["id"] for module in modules}
    assert REQUIRED_MODULE_IDS.issubset(ids)


def test_module_dataset_loads_and_validates() -> None:
    modules = get_training_modules()
    assert len(modules) >= len(REQUIRED_MODULE_IDS)


def test_module_references_valid_exercise_categories_and_names() -> None:
    schema = ModuleSchema()
    modules = load_modules(MODULES_JSON)
    valid_names = build_valid_exercise_name_set(EXERCISES_JSON)
    schema.validate_module_list(modules, valid_names)


def test_rejects_unknown_excluded_exercise_reference() -> None:
    schema = ModuleSchema()
    modules = get_training_modules()
    valid_names = build_valid_exercise_name_set(EXERCISES_JSON)

    bad = modules[0].copy()
    bad["excluded_exercises"] = ["not-a-real-exercise"]

    with pytest.raises(ModuleValidationError):
        schema.validate_module(bad, valid_names)


def test_rejects_invalid_category_reference() -> None:
    schema = ModuleSchema()
    modules = get_training_modules()
    valid_names = build_valid_exercise_name_set(EXERCISES_JSON)

    bad = modules[0].copy()
    bad["preferred_exercise_categories"] = ["bodybuilding_only"]

    with pytest.raises(ModuleValidationError):
        schema.validate_module(bad, valid_names)


def test_rejects_missing_required_field() -> None:
    schema = ModuleSchema()
    modules = get_training_modules()
    valid_names = build_valid_exercise_name_set(EXERCISES_JSON)

    bad = modules[0].copy()
    bad.pop("purpose")

    with pytest.raises(ModuleValidationError):
        schema.validate_module(bad, valid_names)
