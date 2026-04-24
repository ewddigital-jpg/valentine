from __future__ import annotations

from pathlib import Path

from src.enforcement_tracker import EnforcementRecord, EnforcementTracker


def test_enforcement_record_persistence(tmp_path: Path) -> None:
    tracker = EnforcementTracker(tmp_path / "enforcement.json")
    tracker.add_record(
        EnforcementRecord(
            date="2026-04-20",
            structured_meals_status="compliant",
            hydration_status="partial",
            blocked_actions_status="compliant",
            training_completion_status="compliant",
            skipped_sessions=0,
            modified_sessions=0,
            notes="normal day",
        )
    )
    loaded = tracker.load_records()
    assert len(loaded) == 1
    assert loaded[0].hydration_status == "partial"


def test_escalation_triggers_for_repeated_violations(tmp_path: Path) -> None:
    tracker = EnforcementTracker(tmp_path / "enforcement.json")
    for i in range(3):
        tracker.add_record(
            EnforcementRecord(
                date=f"2026-04-2{i}",
                structured_meals_status="violated",
                hydration_status="partial",
                blocked_actions_status="violated",
                training_completion_status="skipped",
                skipped_sessions=1,
                modified_sessions=0,
                notes="binge risk fight_week recovery",
            )
        )
    escalation = tracker.assess_escalation(recent_days=7)
    assert escalation.escalation_flag is True
    assert escalation.escalation_level in {"moderate", "high"}
    assert len(escalation.escalation_actions) >= 2


def test_escalation_uses_nutrition_adherence_patterns(tmp_path: Path) -> None:
    tracker = EnforcementTracker(tmp_path / "enforcement.json")
    for i in range(2):
        tracker.add_record(
            EnforcementRecord(
                date=f"2026-04-2{i}",
                structured_meals_status="partial",
                hydration_status="compliant",
                blocked_actions_status="compliant",
                training_completion_status="compliant",
                skipped_sessions=0,
                modified_sessions=0,
                notes="fight_week",
                protein_target_hit="no",
                meals_followed="no",
                snack_control="chaotic",
                missed_meals_count=2,
                hunger_level_1_to_5=5,
            )
        )
    escalation = tracker.assess_escalation()
    assert escalation.escalation_flag is True
    assert any("Meal structure failures" in reason or "High hunger" in reason for reason in escalation.reasons)
