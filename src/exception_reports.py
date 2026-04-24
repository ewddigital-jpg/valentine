"""Coach-facing exception summaries from audit + enforcement logs."""

from __future__ import annotations

from collections import Counter

from .decision_audit import DecisionAuditEntry
from .enforcement_tracker import EnforcementRecord
from .intervention_state import ActiveIntervention


def build_weekly_exception_report(
    decision_logs: list[DecisionAuditEntry],
    enforcement_logs: list[EnforcementRecord],
    intervention_states: list[ActiveIntervention] | None = None,
) -> dict[str, object]:
    recent_decisions = decision_logs[-7:]
    recent_enforcement = enforcement_logs[-7:]

    triggered_rules = Counter()
    ignored_recommendations = Counter()

    for entry in recent_decisions:
        for rule in entry.enforced_rules:
            triggered_rules[rule] += 1

    for record in recent_enforcement:
        if record.structured_meals_status in {"partial", "violated"}:
            ignored_recommendations["structured_meals"] += 1
        if record.hydration_status in {"partial", "violated"}:
            ignored_recommendations["hydration"] += 1
        if record.blocked_actions_status == "violated":
            ignored_recommendations["blocked_actions"] += 1
        if record.training_completion_status in {"skipped", "violated"}:
            ignored_recommendations["training_completion"] += 1

    what_changed = []
    if recent_decisions:
        modes = [d.mode for d in recent_decisions]
        what_changed.append(f"Modes seen this week: {', '.join(sorted(set(modes)))}")
        nutrition_mods = [d.selected_nutrition_module for d in recent_decisions]
        what_changed.append(f"Nutrition modules used: {', '.join(sorted(set(nutrition_mods)))}")

    repeated_violations = [
        key for key, count in ignored_recommendations.items() if count >= 2
    ]

    intervention_states = intervention_states or []
    active_interventions_this_week = [item.plan.id for item in intervention_states]
    intervention_triggers_this_week = [
        ", ".join(item.plan.trigger_conditions) for item in intervention_states
    ]

    outcome_counter = Counter()
    for item in intervention_states:
        for note in item.notes:
            if "evaluated as:" in note:
                outcome = note.split("evaluated as:")[-1].strip()
                outcome_counter[outcome] += 1

    intervention_outcomes = dict(outcome_counter)
    most_effective = "undetermined"
    if outcome_counter.get("improved", 0) > 0:
        # choose first improved intervention type deterministically by sorted id
        improved_ids = sorted(
            [item.plan.id for item in intervention_states if any("evaluated as: improved" in n for n in item.notes)]
        )
        if improved_ids:
            most_effective = improved_ids[0]

    return {
        "what_changed_this_week_and_why": what_changed,
        "repeated_violation_patterns": repeated_violations,
        "top_repeated_violation_patterns_tied_to_interventions": repeated_violations if intervention_states else [],
        "rules_triggered_most_often": triggered_rules.most_common(5),
        "recommendations_ignored_most_often": ignored_recommendations.most_common(5),
        "active_interventions_this_week": active_interventions_this_week,
        "intervention_triggers_this_week": intervention_triggers_this_week,
        "intervention_outcomes": intervention_outcomes,
        "most_effective_intervention_type": most_effective,
    }
