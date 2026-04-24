from __future__ import annotations

from pathlib import Path

from src.enforcement_tracker import EscalationResult
from src.intervention_engine import InterventionEngine


def test_intervention_starts_from_binge_escalation(tmp_path: Path) -> None:
    engine = InterventionEngine(tmp_path / "intervention.json")
    escalation = EscalationResult(
        escalation_flag=True,
        escalation_level="moderate",
        escalation_actions=["Enforce fixed structure"],
        reasons=["Repeated binge-risk + skipped structure detected."],
    )
    active = engine.maybe_start_intervention("2026-04-23", escalation, warning_flags=[])
    assert active is not None
    assert active.plan.id == "int_binge_structure_3d"
    assert active.plan.duration_days == 3


def test_injection_adds_temporary_rules_and_blocks(tmp_path: Path) -> None:
    engine = InterventionEngine(tmp_path / "intervention.json")
    escalation = EscalationResult(
        escalation_flag=True,
        escalation_level="high",
        escalation_actions=["Escalate"],
        reasons=["Blocked actions repeatedly ignored."],
    )
    engine.maybe_start_intervention("2026-04-23", escalation, warning_flags=[])

    out = {
        "training_recommendation": "explosive_day",
        "enforced_rules": ["Protein floor"],
        "blocked_actions": ["fasting"],
        "meal_timing_focus": ["Protein breakfast"],
        "hydration_target": 3000,
    }
    injected = engine.inject_into_checkin_output(out, today="2026-04-23")
    assert injected["active_intervention"]["id"] == "int_blocked_actions_3d"
    assert "coach-approved meal list only" in injected["enforced_rules"]
    assert "unplanned_snacking" in injected["blocked_actions"]


def test_no_intervention_when_no_escalation(tmp_path: Path) -> None:
    engine = InterventionEngine(tmp_path / "intervention.json")
    escalation = EscalationResult(False, "none", [], ["No escalation trigger threshold met."])
    active = engine.maybe_start_intervention("2026-04-23", escalation, warning_flags=[])
    assert active is None
