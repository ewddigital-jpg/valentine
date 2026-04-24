"""High-level daily planner that combines module selection and session building."""

from __future__ import annotations

from dataclasses import asdict

from .context_models import DailyContext
from .rules_engine import RulesEngine
from .session_builder import SessionBuilder


class DailyPlanner:
    def __init__(self) -> None:
        self.rules_engine = RulesEngine()
        self.session_builder = SessionBuilder()

    def build_daily_plan(self, context: DailyContext) -> dict[str, object]:
        decision = self.rules_engine.select_modules(context)

        session_1 = self.session_builder.build_session(decision.primary_module_id, context)
        session_2_optional = None
        if decision.secondary_module_id is not None:
            session_2_optional = self.session_builder.build_session(decision.secondary_module_id, context)

        readiness_summary = {
            "readiness_score": context.readiness_score,
            "sleep_hours": context.sleep_hours,
            "fatigue": context.fatigue_1_to_5,
            "energy": context.energy_1_to_5,
            "stress": context.stress_1_to_5,
            "days_to_fight": context.days_to_fight,
        }

        recovery_notes = [
            "Hydration and post-session protein/carbs are placeholders for future nutrition module.",
            "Prioritize 7-9h sleep when possible.",
        ]
        if context.days_to_fight <= 7:
            recovery_notes.append("Fight-week mode: reduce non-essential volume and stay sharp.")

        return {
            "selected_module": decision.primary_module_id,
            "module_rationale": decision.rationale,
            "readiness_summary": readiness_summary,
            "session_1": asdict(session_1),
            "session_2_optional": asdict(session_2_optional) if session_2_optional else None,
            "warnings": decision.warnings,
            "recovery_notes": recovery_notes,
        }
