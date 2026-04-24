"""Weekly microcycle planner with deterministic sequencing and adaptation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .compliance_tracker import ComplianceTracker
from .microcycle_rules import (
    HIGH_FATIGUE_MODULES,
    RECOVERY_SUPPORT_MODULES,
    TECHNIQUE_MODULES,
    WeekRuleConfig,
    module_priority,
    violates_spacing,
)
from .state_models import PlannedSession, WeeklyState, week_start_from_date


@dataclass(frozen=True)
class WeeklyContext:
    week_start: date
    days_to_fight: int
    fixed_boxing_gym_days: list[int]  # Monday=0..Sunday=6
    allow_double_sessions: bool
    prior_week_load_score: float
    lower_body_soreness_1_to_5: int = 2


class WeeklyPlanner:
    def __init__(self) -> None:
        self.compliance = ComplianceTracker()

    def generate_weekly_plan(self, context: WeeklyContext, existing_state: WeeklyState | None = None) -> dict[str, object]:
        config = WeekRuleConfig(days_to_fight=context.days_to_fight)
        plan: list[PlannedSession] = []
        warnings: list[str] = []

        template = self._base_template(context.days_to_fight)
        high_fatigue_count = 0
        prev_module: str | None = None

        for day_idx in range(7):
            day = context.week_start + timedelta(days=day_idx)
            module_id = template[day_idx]
            rationale = "Base weekly structure."

            if day_idx == 6:
                module_id = "active_recovery_day"
                rationale = "Sunday defaults to rest/light recovery."

            if day_idx in context.fixed_boxing_gym_days and module_id not in TECHNIQUE_MODULES:
                module_id = "technical_day"
                rationale = "Anchored to fixed boxing gym technical exposure."

            if context.days_to_fight <= 7 and module_id in HIGH_FATIGUE_MODULES:
                module_id = "fight_week_sharpening_day"
                rationale = "Fight-week bias reduced fatigue and increased sharpness focus."

            if context.lower_body_soreness_1_to_5 >= 4 and module_id in {"strength_day_lower", "explosive_day"}:
                module_id = "technical_day"
                rationale = "Lower-body soreness replaced heavy/lower explosive loading."

            if violates_spacing(prev_module, module_id):
                module_id = "technical_day" if module_id != "technical_day" else "active_recovery_day"
                rationale = "Spacing rule prevented high-fatigue stacking."

            if module_id in HIGH_FATIGUE_MODULES:
                high_fatigue_count += 1
            if high_fatigue_count > config.high_fatigue_cap:
                module_id = "aerobic_base_day"
                rationale = "High-fatigue cap exceeded; swapped to recovery-support load."
                high_fatigue_count -= 1

            double_ok = (
                context.allow_double_sessions
                and module_priority(module_id, context.days_to_fight, day_idx) == "high"
                and module_id not in RECOVERY_SUPPORT_MODULES
                and day_idx not in {5, 6}
            )

            plan.append(
                PlannedSession(
                    date=day.isoformat(),
                    module_id=module_id,
                    rationale=rationale,
                    priority=module_priority(module_id, context.days_to_fight, day_idx),
                    double_session=double_ok,
                )
            )
            prev_module = module_id

        self._enforce_minimum_exposures(plan, warnings)

        week_state = existing_state or WeeklyState(week_start=week_start_from_date(context.week_start))
        week_state.planned_sessions = plan
        week_state.notes.append(f"Generated weekly plan with fight proximity {context.days_to_fight} days.")

        fatigue_budget = {
            "high_fatigue_days": len([s for s in plan if s.module_id in HIGH_FATIGUE_MODULES]),
            "recovery_support_days": len([s for s in plan if s.module_id in RECOVERY_SUPPORT_MODULES]),
            "double_session_days": len([s for s in plan if s.double_session]),
            "prior_week_load_score": context.prior_week_load_score,
        }

        return {
            "week_start": week_state.week_start,
            "day_by_day_module_plan": [s.__dict__ for s in plan],
            "fatigue_budget_summary": fatigue_budget,
            "warnings": warnings,
            "session_priority_ranking": {s.date: s.priority for s in plan},
            "state": week_state,
        }

    def adjust_remaining_week(
        self,
        state: WeeklyState,
        current_day_index: int,
        days_to_fight: int,
        high_fatigue_flag: bool,
    ) -> WeeklyState:
        skipped_key = {s.module_id for s in state.skipped_sessions if s.module_id in {"explosive_day", "technical_day"}}

        for idx, planned in enumerate(state.planned_sessions):
            if idx <= current_day_index:
                continue

            if high_fatigue_flag and planned.module_id in HIGH_FATIGUE_MODULES:
                planned.module_id = "active_recovery_day"
                planned.rationale = "Adjusted due to high accumulated fatigue."

            if days_to_fight <= 7 and planned.module_id in HIGH_FATIGUE_MODULES:
                planned.module_id = "fight_week_sharpening_day"
                planned.rationale = "Fight-week adjustment reduced load."

            if "explosive_day" in skipped_key:
                if planned.module_id == "aerobic_base_day" and not high_fatigue_flag and days_to_fight > 10:
                    planned.module_id = "explosive_day"
                    planned.rationale = "Reinserted missed key explosive session safely."
                    skipped_key.remove("explosive_day")
                else:
                    state.notes.append("Missed explosive session was not force-stacked later (make-up chaos prevention).")

        return state

    def _base_template(self, days_to_fight: int) -> list[str]:
        if days_to_fight <= 7:
            return [
                "fight_week_sharpening_day",
                "technical_day",
                "aerobic_base_day",
                "technical_day",
                "fight_week_sharpening_day",
                "active_recovery_day",
                "active_recovery_day",
            ]
        return [
            "explosive_day",
            "technical_day",
            "strength_day_lower",
            "boxing_conditioning_day",
            "aerobic_base_day",
            "strength_day_upper_rotation",
            "active_recovery_day",
        ]

    def _enforce_minimum_exposures(self, plan: list[PlannedSession], warnings: list[str]) -> None:
        if not any(item.module_id in TECHNIQUE_MODULES for item in plan):
            plan[1].module_id = "technical_day"
            plan[1].rationale = "Inserted minimum technique exposure."
            warnings.append("Technique exposure was missing and has been inserted.")

        if not any(item.module_id in RECOVERY_SUPPORT_MODULES for item in plan):
            plan[4].module_id = "aerobic_base_day"
            plan[4].rationale = "Inserted recovery-support exposure."
            warnings.append("Recovery-support exposure was missing and has been inserted.")
