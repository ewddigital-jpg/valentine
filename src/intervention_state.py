"""State model and JSON persistence for short-horizon interventions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass(frozen=True)
class InterventionPlan:
    id: str
    trigger_conditions: list[str]
    duration_days: int
    temporary_rules: list[str]
    blocked_actions: list[str]
    meal_structure_changes: list[str]
    training_complexity_changes: list[str]
    hydration_changes: list[str]
    rationale: list[str]
    success_metrics: list[str]


@dataclass
class ActiveIntervention:
    plan: InterventionPlan
    start_date: str
    end_date: str
    active: bool = True
    compliance_snapshots: list[dict[str, object]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "plan": asdict(self.plan),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "active": self.active,
            "compliance_snapshots": self.compliance_snapshots,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ActiveIntervention":
        return cls(
            plan=InterventionPlan(**data["plan"]),
            start_date=str(data["start_date"]),
            end_date=str(data["end_date"]),
            active=bool(data.get("active", True)),
            compliance_snapshots=list(data.get("compliance_snapshots", [])),
            notes=[str(x) for x in data.get("notes", [])],
        )


class InterventionStateStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, active: ActiveIntervention) -> None:
        self.file_path.write_text(json.dumps(active.to_dict(), indent=2), encoding="utf-8")

    def load(self) -> ActiveIntervention | None:
        if not self.file_path.exists():
            return None
        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        return ActiveIntervention.from_dict(raw)
