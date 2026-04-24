"""Build deterministic session blueprints from module + exercise data."""

from __future__ import annotations

from dataclasses import dataclass

from .context_models import DailyContext
from .module_loader import get_training_modules
from .sample_data import get_starter_exercises


@dataclass(frozen=True)
class SessionBlueprint:
    warmup: list[str]
    main_block: list[str]
    secondary_block: list[str]
    finisher: list[str]
    optional_core_mobility: list[str]
    estimated_session_duration: int
    rationale: list[str]


class SessionBuilder:
    def __init__(self) -> None:
        self.exercises = get_starter_exercises()
        self.modules = {module["id"]: module for module in get_training_modules()}

    def build_session(self, module_id: str, context: DailyContext) -> SessionBlueprint:
        module = self.modules[module_id]
        candidates = self._filter_candidates(module, context)

        warmup = self._pick(candidates, {"mobility", "footwork", "recovery"}, count=2)
        main_block = self._pick(candidates, set(module["preferred_exercise_categories"]), count=3)
        secondary_block = self._pick(candidates, {"boxing_specific", "trunk_stability", "reaction", "aerobic_base"}, count=2)
        finisher = self._pick(candidates, {"boxing_specific", "conditioning_boxing_specific", "recovery"}, count=1)
        core_mobility = self._pick(candidates, {"trunk_stability", "mobility", "recovery"}, count=1)

        if context.time_available_min < 40:
            main_block = main_block[:2]
            secondary_block = secondary_block[:1]
            finisher = []

        if context.days_to_fight <= 7:
            main_block = main_block[:2]
            secondary_block = secondary_block[:1]

        duration = self._estimate_duration(context, main_block, secondary_block, finisher)
        rationale = [
            f"Selected exercises from categories: {', '.join(module['preferred_exercise_categories'])}.",
            "Sorted by boxing transfer, weakness relevance, and fatigue fit.",
        ]

        return SessionBlueprint(
            warmup=warmup,
            main_block=main_block,
            secondary_block=secondary_block,
            finisher=finisher,
            optional_core_mobility=core_mobility,
            estimated_session_duration=duration,
            rationale=rationale,
        )

    def _filter_candidates(self, module: dict[str, object], context: DailyContext) -> list[dict[str, object]]:
        excluded_categories = set(module["excluded_categories"])
        excluded_exercises = set(module["excluded_exercises"])
        preferred = set(module["preferred_exercise_categories"])

        candidates = []
        for exercise in self.exercises:
            name = str(exercise["name"])
            category = str(exercise["category"])
            if category in excluded_categories or name in excluded_exercises:
                continue
            if not self._location_ok(exercise, context):
                continue
            if not self._equipment_ok(exercise, context):
                continue

            fatigue = int(exercise["fatigue_cost"])
            min_fatigue, max_fatigue = module["target_fatigue_range"]
            fatigue_mismatch = 0 if min_fatigue <= fatigue <= max_fatigue else 1

            score = 0
            score += int(exercise["boxing_transfer_score"]) * 3
            if category in preferred:
                score += 4
            if "explosiveness" in exercise["best_for_weaknesses"]:
                score += 2
            if "defensive_reactions" in exercise["best_for_weaknesses"]:
                score += 2
            if "solo" in exercise["locations"] and context.location_today != "boxing_gym":
                score += 1
            score -= fatigue_mismatch
            score -= int(exercise["fatigue_cost"])

            candidates.append({"exercise": exercise, "score": score})

        candidates.sort(key=lambda item: (-item["score"], item["exercise"]["name"]))
        return [item["exercise"] for item in candidates]

    def _pick(self, exercises: list[dict[str, object]], categories: set[str], count: int) -> list[str]:
        chosen: list[str] = []
        for exercise in exercises:
            if str(exercise["category"]) not in categories:
                continue
            name = str(exercise["name"])
            if name not in chosen:
                chosen.append(name)
            if len(chosen) == count:
                break
        return chosen

    def _estimate_duration(
        self,
        context: DailyContext,
        main_block: list[str],
        secondary_block: list[str],
        finisher: list[str],
    ) -> int:
        duration = 15 + len(main_block) * 12 + len(secondary_block) * 8 + len(finisher) * 6
        return min(duration, context.time_available_min)

    def _location_ok(self, exercise: dict[str, object], context: DailyContext) -> bool:
        locations = set(exercise["locations"])
        if context.location_today == "boxing_gym":
            return "gym" in locations or "solo" in locations
        if context.location_today == "gym":
            return "gym" in locations
        if context.location_today == "park":
            return "park" in locations or "solo" in locations
        return "solo" in locations

    def _equipment_ok(self, exercise: dict[str, object], context: DailyContext) -> bool:
        needed = set(exercise["equipment_needed"])
        if needed == {"none"}:
            return True
        available = set(context.equipment_today)
        return needed.issubset(available)
