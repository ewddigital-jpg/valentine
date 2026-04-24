"""Deterministic module selection logic for daily boxing planning."""

from __future__ import annotations

from dataclasses import dataclass

from .context_models import DailyContext
from .module_loader import get_training_modules
from .sample_data import get_starter_exercises


@dataclass(frozen=True)
class ModuleDecision:
    primary_module_id: str
    secondary_module_id: str | None
    rationale: list[str]
    warnings: list[str]


class RulesEngine:
    def __init__(self) -> None:
        self.modules = get_training_modules()
        self.exercises = get_starter_exercises()
        self._module_map = {module["id"]: module for module in self.modules}

    def select_modules(self, context: DailyContext) -> ModuleDecision:
        warnings: list[str] = []
        rationale: list[str] = []

        if context.is_sunday and "allow_light" not in context.notes.lower():
            warnings.append("Sunday defaulted to rest/light recovery logic.")
            rationale.append("Sunday rule prefers recovery unless explicitly overridden.")
            return ModuleDecision("active_recovery_day", None, rationale, warnings)

        scored: list[tuple[str, float]] = []
        for module in self.modules:
            module_id = str(module["id"])
            valid, reason = self._passes_hard_rules(module_id, context)
            if not valid:
                continue
            score = self._soft_score(module_id, context)
            scored.append((module_id, score))

        if not scored:
            warnings.append("No module met all hard rules; fell back to active recovery.")
            rationale.append("Safety fallback when readiness/context conflicts are high.")
            return ModuleDecision("active_recovery_day", None, rationale, warnings)

        scored.sort(key=lambda item: (-item[1], item[0]))
        primary = scored[0][0]
        rationale.append(f"Primary module selected by highest deterministic score: {primary}.")

        if context.days_to_fight <= 7 and primary not in {"fight_week_sharpening_day", "technical_day", "active_recovery_day"}:
            primary = "fight_week_sharpening_day"
            rationale.append("Fight proximity (<=7 days) shifted selection toward sharpening module.")

        secondary = self._secondary_module(primary, context)
        if secondary:
            rationale.append(f"Secondary light module allowed due to double-session readiness: {secondary}.")

        return ModuleDecision(primary, secondary, rationale, warnings)

    def _passes_hard_rules(self, module_id: str, context: DailyContext) -> tuple[bool, str]:
        if context.days_to_fight <= 3 and module_id in {"strength_day_lower", "boxing_conditioning_day"}:
            return False, "Too close to fight for heavy lower/conditioning load."

        if context.fatigue_1_to_5 >= 4 and context.sleep_hours < 6.5:
            if module_id not in {"active_recovery_day", "technical_day"}:
                return False, "High fatigue + poor sleep hard filter."

        if context.yesterday_had_sparring and module_id in {"strength_day_lower", "boxing_conditioning_day", "explosive_day"}:
            clearly_good = (
                context.energy_1_to_5 >= 4
                and context.fatigue_1_to_5 <= 2
                and context.soreness_lower_1_to_5 <= 2
            )
            if not clearly_good:
                return False, "Day after sparring requires conservative loading."

        if context.soreness_lower_1_to_5 >= 4 and module_id in {"strength_day_lower", "explosive_day", "boxing_conditioning_day"}:
            return False, "Lower-body soreness hard filter."

        if context.time_available_min < 40 and module_id not in {"technical_day", "explosive_day", "active_recovery_day", "fight_week_sharpening_day"}:
            return False, "Short session hard filter."

        if context.location_today in {"home", "park"} and module_id in {"strength_day_lower", "strength_day_upper_rotation"}:
            if "dumbbells" not in context.equipment_today and "resistance_band" not in context.equipment_today:
                return False, "Location/equipment hard filter for strength modules."

        if context.boxing_gym_session_fixed and module_id == "aerobic_base_day":
            return False, "Gym session fixed; prioritize boxing-oriented module."

        return True, "ok"

    def _soft_score(self, module_id: str, context: DailyContext) -> float:
        score = 0.0
        readiness = context.readiness_score

        if module_id == "explosive_day":
            if readiness >= 3.0 and context.days_to_fight > 7 and context.soreness_lower_1_to_5 <= 2:
                score += 6.0
            if context.yesterday_had_run:
                score -= 2.0

        if module_id == "technical_day":
            if context.fatigue_1_to_5 in {2, 3}:
                score += 4.0
            if context.stress_1_to_5 >= 3:
                score += 1.0

        if module_id == "boxing_conditioning_day":
            if context.days_to_fight > 7 and readiness >= 2.5:
                score += 5.0
            if context.yesterday_had_sprints:
                score -= 2.0

        if module_id == "aerobic_base_day":
            if context.fatigue_1_to_5 >= 3 or context.stress_1_to_5 >= 4:
                score += 3.5
            if context.yesterday_had_run:
                score -= 1.5

        if module_id == "fight_week_sharpening_day":
            if 1 <= context.days_to_fight <= 7 and readiness >= 1.5:
                score += 6.5

        if module_id == "active_recovery_day":
            if context.fatigue_1_to_5 >= 4:
                score += 5.0
            if context.sleep_hours < 6.5:
                score += 2.0

        if module_id.startswith("strength_day"):
            if readiness >= 2.5 and context.days_to_fight > 10 and context.yesterday_had_sparring is False:
                score += 3.0

        if context.time_available_min < 40 and module_id in {"technical_day", "explosive_day", "active_recovery_day", "fight_week_sharpening_day"}:
            score += 2.0

        if context.location_today == "park" and module_id in {"aerobic_base_day", "active_recovery_day", "technical_day", "explosive_day"}:
            score += 1.0

        if context.double_session_today and module_id == "technical_day":
            score += 0.5

        return score

    def _secondary_module(self, primary_module_id: str, context: DailyContext) -> str | None:
        if not context.double_session_today:
            return None
        if context.fatigue_1_to_5 >= 4 or context.sleep_hours < 6.5:
            return None
        if context.time_available_min < 75:
            return None
        if primary_module_id in {"active_recovery_day", "post_fight_recovery_day"}:
            return None

        if context.days_to_fight <= 7:
            return "active_recovery_day"
        return "aerobic_base_day"
