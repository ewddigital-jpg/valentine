from __future__ import annotations

from pathlib import Path

from src.checkin_workflow import CheckinInput, CheckinWorkflow
from src.enforcement_tracker import EnforcementRecord, EscalationResult
from src.intervention_bridge import InterventionBridge
from src.intervention_engine import InterventionEngine
from src.intervention_state import InterventionStateStore
from src.intervention_tracker import InterventionTracker


def _checkin_input() -> CheckinInput:
    return CheckinInput(
        bodyweight_kg=72.0,
        sleep_hours=7.0,
        fatigue_1_to_5=2,
        soreness_1_to_5=2,
        energy_1_to_5=4,
        stress_1_to_5=3,
        days_to_fight=20,
        todays_training_plan_module="technical_day",
        yesterday_completion_status="completed",
        recent_bodyweights=[72.4, 72.3, 72.2, 72.1, 72.0],
        fight_weight_target_kg=70.0,
        hunger_1_to_5=4,
        binge_risk_note="binge risk",
    )


def test_bridge_auto_injects_active_intervention(tmp_path: Path) -> None:
    state_path = tmp_path / "intervention.json"
    bridge = InterventionBridge(
        checkin_workflow=CheckinWorkflow(),
        intervention_engine=InterventionEngine(state_path),
        intervention_tracker=InterventionTracker(InterventionStateStore(state_path)),
    )

    escalation = EscalationResult(True, "moderate", ["x"], ["Repeated binge-risk + skipped structure detected."])
    out = bridge.run_daily_checkin(
        date="2026-04-23",
        checkin_input=_checkin_input(),
        escalation=escalation,
        warning_flags=[],
    )

    assert out["active_intervention"] is not None
    assert out["active_intervention"]["id"] == "int_binge_structure_3d"
    assert "fixed breakfast required" in out["enforced_rules"]
    assert "meal_skipping" in out["blocked_actions"]


def test_bridge_auto_snapshots_enforcement_update(tmp_path: Path) -> None:
    state_path = tmp_path / "intervention.json"
    bridge = InterventionBridge(
        checkin_workflow=CheckinWorkflow(),
        intervention_engine=InterventionEngine(state_path),
        intervention_tracker=InterventionTracker(InterventionStateStore(state_path)),
    )

    escalation = EscalationResult(True, "moderate", ["x"], ["Repeated binge-risk + skipped structure detected."])
    bridge.run_daily_checkin(
        date="2026-04-23",
        checkin_input=_checkin_input(),
        escalation=escalation,
        warning_flags=[],
    )

    bridge.record_enforcement_update(
        date="2026-04-23",
        enforcement=EnforcementRecord(
            date="2026-04-23",
            structured_meals_status="partial",
            hydration_status="compliant",
            blocked_actions_status="compliant",
            training_completion_status="compliant",
            skipped_sessions=0,
            modified_sessions=0,
            notes="intervention day",
        ),
        bodyweight_kg=72.0,
    )

    active = InterventionStateStore(state_path).load()
    assert active is not None
    assert len(active.compliance_snapshots) == 1
    assert active.compliance_snapshots[0]["structured_meals_status"] == "partial"
