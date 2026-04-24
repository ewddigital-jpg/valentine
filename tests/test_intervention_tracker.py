from __future__ import annotations

from pathlib import Path

from src.enforcement_tracker import EnforcementRecord, EscalationResult
from src.intervention_engine import InterventionEngine
from src.intervention_state import InterventionStateStore
from src.intervention_tracker import InterventionTracker


def _start_intervention(path: Path) -> InterventionStateStore:
    engine = InterventionEngine(path)
    engine.maybe_start_intervention(
        "2026-04-23",
        EscalationResult(True, "moderate", ["x"], ["Repeated binge-risk + skipped structure detected."]),
        [],
    )
    return InterventionStateStore(path)


def test_intervention_tracker_snapshots_and_evaluates_improved(tmp_path: Path) -> None:
    store = _start_intervention(tmp_path / "intervention.json")
    tracker = InterventionTracker(store)

    tracker.snapshot_day(
        "2026-04-23",
        EnforcementRecord("2026-04-23", "compliant", "compliant", "compliant", "compliant", 0, 0, ""),
        72.0,
    )
    tracker.snapshot_day(
        "2026-04-24",
        EnforcementRecord("2026-04-24", "compliant", "partial", "compliant", "compliant", 0, 0, ""),
        71.9,
    )
    tracker.snapshot_day(
        "2026-04-25",
        EnforcementRecord("2026-04-25", "compliant", "compliant", "compliant", "compliant", 0, 0, ""),
        71.9,
    )

    pre = [
        EnforcementRecord("2026-04-20", "violated", "violated", "violated", "skipped", 1, 0, ""),
        EnforcementRecord("2026-04-21", "violated", "partial", "violated", "violated", 1, 0, ""),
    ]
    eval_result = tracker.evaluate(pre, pre_weights=[72.5, 72.6, 72.4])
    assert eval_result.status in {"improved", "unchanged"}
    assert eval_result.training_completion_rate >= 0.6


def test_intervention_tracker_evaluates_worse_when_completion_drops(tmp_path: Path) -> None:
    store = _start_intervention(tmp_path / "intervention.json")
    tracker = InterventionTracker(store)

    tracker.snapshot_day(
        "2026-04-23",
        EnforcementRecord("2026-04-23", "violated", "violated", "violated", "skipped", 1, 0, ""),
        72.0,
    )
    tracker.snapshot_day(
        "2026-04-24",
        EnforcementRecord("2026-04-24", "violated", "violated", "violated", "violated", 1, 0, ""),
        72.6,
    )

    pre = [EnforcementRecord("2026-04-21", "partial", "partial", "partial", "compliant", 0, 0, "")]
    result = tracker.evaluate(pre, pre_weights=[72.2, 72.1])
    assert result.status == "worse"
