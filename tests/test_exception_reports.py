from __future__ import annotations

from src.decision_audit import DecisionAuditEntry
from src.enforcement_tracker import EnforcementRecord
from src.exception_reports import build_weekly_exception_report
from src.intervention_state import ActiveIntervention, InterventionPlan


def test_exception_report_summarizes_patterns() -> None:
    decisions = [
        DecisionAuditEntry(
            date="2026-04-20",
            mode="NORMAL_CUT",
            selected_training_module="explosive_day",
            selected_nutrition_module="explosive_day_food",
            weight_status="on_track",
            enforced_rules=["Protein floor", "Hydration floor"],
            blocked_actions=["fasting"],
            behavior_adjustments=["maintain"],
            warning_flags=[],
            rationale=["standard"],
        ),
        DecisionAuditEntry(
            date="2026-04-21",
            mode="FIGHT_WEEK",
            selected_training_module="technical_day",
            selected_nutrition_module="fight_week_day_food",
            weight_status="slightly_behind",
            enforced_rules=["Hydration floor"],
            blocked_actions=["aggressive_calorie_cut"],
            behavior_adjustments=["structured meals"],
            warning_flags=["fight week"],
            rationale=["fight week"],
        ),
    ]
    enforcement = [
        EnforcementRecord(
            date="2026-04-20",
            structured_meals_status="violated",
            hydration_status="partial",
            blocked_actions_status="violated",
            training_completion_status="compliant",
            skipped_sessions=0,
            modified_sessions=0,
            notes="binge risk",
        ),
        EnforcementRecord(
            date="2026-04-21",
            structured_meals_status="violated",
            hydration_status="partial",
            blocked_actions_status="violated",
            training_completion_status="skipped",
            skipped_sessions=1,
            modified_sessions=0,
            notes="fight_week",
        ),
    ]

    interventions = [
        ActiveIntervention(
            plan=InterventionPlan(
                id="int_binge_structure_3d",
                trigger_conditions=["binge risk + skipped structured meals"],
                duration_days=3,
                temporary_rules=["fixed breakfast required"],
                blocked_actions=["meal_skipping"],
                meal_structure_changes=["4 feeding events"],
                training_complexity_changes=["no second session"],
                hydration_changes=["hydration floor increased"],
                rationale=["restore structure"],
                success_metrics=["compliance up"],
            ),
            start_date="2026-04-20",
            end_date="2026-04-22",
            active=False,
            notes=["Intervention evaluated as: improved"],
        )
    ]

    report = build_weekly_exception_report(decisions, enforcement, interventions)
    assert "repeated_violation_patterns" in report
    assert "structured_meals" in report["repeated_violation_patterns"]
    assert len(report["rules_triggered_most_often"]) >= 1
    assert report["most_effective_intervention_type"] == "int_binge_structure_3d"
