"""Load and validate training modules against exercise source data."""

from __future__ import annotations

from pathlib import Path

from .module_schema import ModuleSchema, build_valid_exercise_name_set, load_modules


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODULES_PATH = ROOT_DIR / "src" / "training_modules.json"
DEFAULT_EXERCISES_PATH = ROOT_DIR / "src" / "exercises.json"


def get_training_modules() -> list[dict[str, object]]:
    """Load modules and validate references to exercise names/categories."""
    modules = load_modules(DEFAULT_MODULES_PATH)
    valid_exercise_names = build_valid_exercise_name_set(DEFAULT_EXERCISES_PATH)
    schema = ModuleSchema()
    schema.validate_module_list(modules, valid_exercise_names)
    return modules


if __name__ == "__main__":
    loaded = get_training_modules()
    print(f"Loaded and validated {len(loaded)} training modules from {DEFAULT_MODULES_PATH}")
