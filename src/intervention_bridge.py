"""Auto-bridge between check-in workflow and intervention lifecycle."""

from __future__ import annotations

from .checkin_workflow import CheckinInput, CheckinWorkflow
from .enforcement_tracker import EnforcementRecord, EscalationResult
from .intervention_engine import InterventionEngine
from .intervention_tracker import InterventionTracker


class InterventionBridge:
    def __init__(
        self,
        checkin_workflow: CheckinWorkflow,
        intervention_engine: InterventionEngine,
        intervention_tracker: InterventionTracker,
    ) -> None:
        self.checkin_workflow = checkin_workflow
        self.intervention_engine = intervention_engine
        self.intervention_tracker = intervention_tracker

    def run_daily_checkin(
        self,
        date: str,
        checkin_input: CheckinInput,
        escalation: EscalationResult,
        warning_flags: list[str],
    ) -> dict[str, object]:
        self.intervention_engine.maybe_start_intervention(
            date=date,
            escalation=escalation,
            warning_flags=warning_flags,
        )
        output = self.checkin_workflow.run(checkin_input)
        output = self.intervention_engine.inject_into_checkin_output(output, today=date)
        return output

    def record_enforcement_update(
        self,
        date: str,
        enforcement: EnforcementRecord,
        bodyweight_kg: float,
    ) -> None:
        # automatic intervention snapshot capture (no extra manual step)
        self.intervention_tracker.record_from_enforcement_update(
            date=date,
            enforcement=enforcement,
            bodyweight_kg=bodyweight_kg,
        )
