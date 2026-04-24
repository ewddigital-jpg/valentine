from __future__ import annotations

from pathlib import Path

from src.decision_audit import DecisionAuditEntry, DecisionAuditStore


def test_decision_audit_logs_and_loads_entry(tmp_path: Path) -> None:
    store = DecisionAuditStore(tmp_path / "decision_audit.json")
    entry = DecisionAuditEntry(
        date="2026-04-23",
        mode="FIGHT_WEEK",
        selected_training_module="technical_day",
        selected_nutrition_module="fight_week_day_food",
        weight_status="slightly_behind",
        enforced_rules=["Protein >= 130g"],
        blocked_actions=["aggressive_calorie_cut"],
        behavior_adjustments=["4 feeding events"],
        warning_flags=["fight-week conservative"],
        rationale=["Mode selected from days_to_fight."],
    )
    store.log_decision(entry)
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].mode == "FIGHT_WEEK"
    assert loaded[0].selected_nutrition_module == "fight_week_day_food"
