"""Track intervention effects and evaluate short-horizon outcomes."""

from __future__ import annotations

from dataclasses import dataclass

from .enforcement_tracker import EnforcementRecord
from .intervention_state import ActiveIntervention, InterventionStateStore


@dataclass(frozen=True)
class InterventionEvaluation:
    status: str  # improved | unchanged | worse
    violation_reduction: float
    bodyweight_stability_delta: float
    training_completion_rate: float
    rationale: list[str]


class InterventionTracker:
    def __init__(self, state_store: InterventionStateStore) -> None:
        self.state_store = state_store

    def snapshot_day(
        self,
        date: str,
        enforcement: EnforcementRecord,
        bodyweight_kg: float,
    ) -> ActiveIntervention | None:
        active = self.state_store.load()
        if active is None or not active.active:
            return None
        active.compliance_snapshots.append(
            {
                "date": date,
                "structured_meals_status": enforcement.structured_meals_status,
                "hydration_status": enforcement.hydration_status,
                "blocked_actions_status": enforcement.blocked_actions_status,
                "training_completion_status": enforcement.training_completion_status,
                "bodyweight_kg": bodyweight_kg,
            }
        )
        self.state_store.save(active)
        return active

    def record_from_enforcement_update(
        self,
        date: str,
        enforcement: EnforcementRecord,
        bodyweight_kg: float,
    ) -> ActiveIntervention | None:
        """Auto-hook used by bridge: snapshot if intervention is active."""
        return self.snapshot_day(date, enforcement, bodyweight_kg)

    def evaluate(
        self,
        pre_intervention_records: list[EnforcementRecord],
        pre_weights: list[float],
    ) -> InterventionEvaluation:
        active = self.state_store.load()
        if active is None:
            return InterventionEvaluation("unchanged", 0.0, 0.0, 0.0, ["No active intervention state found."])

        post = active.compliance_snapshots
        pre_violations = _count_violations(pre_intervention_records)
        post_violations = _count_snapshot_violations(post)

        if pre_violations == 0:
            violation_reduction = 0.0
        else:
            violation_reduction = round((pre_violations - post_violations) / pre_violations, 3)

        pre_stability = _weight_range(pre_weights)
        post_stability = _weight_range([float(x["bodyweight_kg"]) for x in post])
        bodyweight_stability_delta = round(pre_stability - post_stability, 3)

        training_completion_rate = _completion_rate(post)

        rationale: list[str] = [
            f"Violation reduction: {violation_reduction}",
            f"Bodyweight stability delta: {bodyweight_stability_delta}",
            f"Training completion rate: {training_completion_rate}",
        ]

        status = "unchanged"
        if violation_reduction >= 0.3 and training_completion_rate >= 0.7 and bodyweight_stability_delta >= 0:
            status = "improved"
        elif violation_reduction < 0 or training_completion_rate < 0.5:
            status = "worse"

        active.active = False
        active.notes.append(f"Intervention evaluated as: {status}")
        self.state_store.save(active)

        return InterventionEvaluation(
            status=status,
            violation_reduction=violation_reduction,
            bodyweight_stability_delta=bodyweight_stability_delta,
            training_completion_rate=training_completion_rate,
            rationale=rationale,
        )


def _count_violations(records: list[EnforcementRecord]) -> int:
    count = 0
    for r in records:
        if r.structured_meals_status == "violated":
            count += 1
        if r.blocked_actions_status == "violated":
            count += 1
        if r.hydration_status == "violated":
            count += 1
    return count


def _count_snapshot_violations(snaps: list[dict[str, object]]) -> int:
    count = 0
    for s in snaps:
        if s.get("structured_meals_status") == "violated":
            count += 1
        if s.get("blocked_actions_status") == "violated":
            count += 1
        if s.get("hydration_status") == "violated":
            count += 1
    return count


def _weight_range(weights: list[float]) -> float:
    if not weights:
        return 0.0
    return round(max(weights) - min(weights), 3)


def _completion_rate(snaps: list[dict[str, object]]) -> float:
    if not snaps:
        return 0.0
    completed = sum(1 for s in snaps if s.get("training_completion_status") == "compliant")
    return round(completed / len(snaps), 3)
