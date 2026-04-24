"""Generate and inject deterministic short-horizon intervention plans."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from .enforcement_tracker import EscalationResult
from .intervention_state import (
    ActiveIntervention,
    InterventionPlan,
    InterventionStateStore,
)


DEFAULT_DURATION_DAYS = 3


class InterventionEngine:
    def __init__(self, state_path: Path) -> None:
        self.store = InterventionStateStore(state_path)

    def maybe_start_intervention(
        self,
        date: str,
        escalation: EscalationResult,
        warning_flags: list[str],
    ) -> ActiveIntervention | None:
        active = self.store.load()
        if active is not None and active.active:
            return active

        if not escalation.escalation_flag and not _high_risk_fight_week(warning_flags):
            return None

        plan = self._plan_from_escalation(escalation, warning_flags)
        start = _parse_date(date)
        end = start + timedelta(days=plan.duration_days - 1)

        active = ActiveIntervention(
            plan=plan,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
            active=True,
            notes=["Intervention started from escalation output."],
        )
        self.store.save(active)
        return active

    def inject_into_checkin_output(
        self,
        checkin_output: dict[str, object],
        today: str,
    ) -> dict[str, object]:
        active = self.store.load()
        if active is None or not active.active:
            checkin_output["active_intervention"] = None
            return checkin_output

        today_d = _parse_date(today)
        if today_d > _parse_date(active.end_date):
            active.active = False
            active.notes.append("Intervention window ended.")
            self.store.save(active)
            checkin_output["active_intervention"] = None
            return checkin_output

        enforced = list(checkin_output.get("enforced_rules", [])) + active.plan.temporary_rules
        blocked = list(checkin_output.get("blocked_actions", [])) + active.plan.blocked_actions
        meal_focus = list(checkin_output.get("meal_timing_focus", [])) + active.plan.meal_structure_changes

        checkin_output["enforced_rules"] = _dedupe(enforced)
        checkin_output["blocked_actions"] = _dedupe(blocked)
        checkin_output["meal_timing_focus"] = _dedupe(meal_focus)
        checkin_output["training_recommendation"] = self._adjust_training(
            str(checkin_output.get("training_recommendation", "technical_day")),
            active.plan.training_complexity_changes,
        )
        checkin_output["hydration_target"] = _apply_hydration_change(
            int(checkin_output.get("hydration_target", 0)),
            active.plan.hydration_changes,
        )
        checkin_output["active_intervention"] = {
            "id": active.plan.id,
            "start_date": active.start_date,
            "end_date": active.end_date,
            "success_metrics": active.plan.success_metrics,
        }
        return checkin_output

    def _plan_from_escalation(
        self,
        escalation: EscalationResult,
        warning_flags: list[str],
    ) -> InterventionPlan:
        reason_text = " | ".join(escalation.reasons).lower()
        warnings_text = " | ".join(warning_flags).lower()

        if "binge" in reason_text:
            return _binge_structure_plan()
        if "under-eating" in reason_text or "low appetite" in warnings_text:
            return _low_appetite_fatigue_plan()
        if "blocked actions" in reason_text:
            return _blocked_actions_plan()
        if "fight" in reason_text or _high_risk_fight_week(warning_flags):
            return _fight_week_chaos_plan()
        if "stress" in warnings_text or "plateau" in warnings_text:
            return _plateau_stress_plan()
        return _generic_structure_plan()

    def _adjust_training(self, current: str, changes: list[str]) -> str:
        if any("reduce training complexity" in c.lower() for c in changes):
            return "technical_day"
        if any("no second session" in c.lower() for c in changes):
            return current
        return current


def _high_risk_fight_week(warnings: list[str]) -> bool:
    text = " | ".join(warnings).lower()
    return "fight-week" in text and "risk" in text


def _apply_hydration_change(current_ml: int, hydration_changes: list[str]) -> int:
    if any("increased" in item.lower() for item in hydration_changes):
        return int(current_ml * 1.1)
    return current_ml


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _binge_structure_plan() -> InterventionPlan:
    return InterventionPlan(
        id="int_binge_structure_3d",
        trigger_conditions=["binge risk + skipped structured meals"],
        duration_days=DEFAULT_DURATION_DAYS,
        temporary_rules=["fixed breakfast required", "fixed lunch required", "mandatory evening protein meal", "no freestyle snacks"],
        blocked_actions=["meal_skipping", "fasting", "unplanned_takeaway_binge"],
        meal_structure_changes=["4 feeding events daily", "pre-logged evening meal"],
        training_complexity_changes=["no second session"],
        hydration_changes=["hydration floor increased"],
        rationale=["Restore eating structure and reduce binge probability."],
        success_metrics=["3-day structured meal compliance >= 80%", "no binge incidents"],
    )


def _low_appetite_fatigue_plan() -> InterventionPlan:
    return InterventionPlan(
        id="int_low_appetite_fatigue_3d",
        trigger_conditions=["high fatigue + low appetite"],
        duration_days=DEFAULT_DURATION_DAYS,
        temporary_rules=["simplified meal options only", "pre-training carbs required"],
        blocked_actions=["deficit_tightening", "double_session_training"],
        meal_structure_changes=["liquid+easy-digest meals around training"],
        training_complexity_changes=["reduce training complexity"],
        hydration_changes=["hydration floor increased"],
        rationale=["Protect recovery while maintaining minimum intake."],
        success_metrics=["fatigue trend stable/down", "meal completion >= 75%"],
    )


def _plateau_stress_plan() -> InterventionPlan:
    return InterventionPlan(
        id="int_plateau_stress_3d",
        trigger_conditions=["weight plateau + high stress"],
        duration_days=DEFAULT_DURATION_DAYS,
        temporary_rules=["no deficit tightening", "fixed protein feedings"],
        blocked_actions=["aggressive_calorie_cut", "extra_high_stress_cardio"],
        meal_structure_changes=["simple repeat meal template"],
        training_complexity_changes=["reduce training complexity"],
        hydration_changes=["maintain hydration floor"],
        rationale=["Break stress-driven plateau without adding pressure."],
        success_metrics=["stress markers stable", "no additional compliance drop"],
    )


def _blocked_actions_plan() -> InterventionPlan:
    return InterventionPlan(
        id="int_blocked_actions_3d",
        trigger_conditions=["repeated blocked-action violations"],
        duration_days=DEFAULT_DURATION_DAYS,
        temporary_rules=["coach-approved meal list only", "fixed check-in after dinner"],
        blocked_actions=["restricted_trigger_food_environment", "unplanned_snacking"],
        meal_structure_changes=["only school/work-friendly options"],
        training_complexity_changes=["no second session"],
        hydration_changes=["hydration floor increased"],
        rationale=["Reduce decision fatigue and remove trigger exposures."],
        success_metrics=["blocked-action violations reduced by >=50%"],
    )


def _fight_week_chaos_plan() -> InterventionPlan:
    return InterventionPlan(
        id="int_fight_week_stability_3d",
        trigger_conditions=["fight-week chaos / high-risk check-ins"],
        duration_days=DEFAULT_DURATION_DAYS,
        temporary_rules=["fixed breakfast required", "pre-training carbs required", "no deficit tightening"],
        blocked_actions=["aggressive_dehydration", "experimental_foods", "double_session_training"],
        meal_structure_changes=["low-residue predictable menu"],
        training_complexity_changes=["reduce training complexity"],
        hydration_changes=["hydration floor increased"],
        rationale=["Stabilize fight-week execution and avoid late chaos."],
        success_metrics=["no blocked-action incidents", "training completion >= 80%"],
    )


def _generic_structure_plan() -> InterventionPlan:
    return InterventionPlan(
        id="int_generic_structure_3d",
        trigger_conditions=["general escalation"],
        duration_days=DEFAULT_DURATION_DAYS,
        temporary_rules=["fixed breakfast required", "no freestyle snacks"],
        blocked_actions=["meal_skipping"],
        meal_structure_changes=["repeatable meal template"],
        training_complexity_changes=["no second session"],
        hydration_changes=["hydration floor increased"],
        rationale=["Short-horizon structure reset."],
        success_metrics=["overall compliance trend improved"],
    )
