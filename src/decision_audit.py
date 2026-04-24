"""Decision audit logging for daily planning/check-in outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class DecisionAuditEntry:
    date: str
    mode: str
    selected_training_module: str
    selected_nutrition_module: str
    weight_status: str
    enforced_rules: list[str]
    blocked_actions: list[str]
    behavior_adjustments: list[str]
    warning_flags: list[str]
    rationale: list[str]


class DecisionAuditStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(self, entry: DecisionAuditEntry) -> None:
        logs = self.load_all()
        logs.append(entry)
        self.file_path.write_text(
            json.dumps([asdict(item) for item in logs], indent=2), encoding="utf-8"
        )

    def load_all(self) -> list[DecisionAuditEntry]:
        if not self.file_path.exists():
            return []
        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        out: list[DecisionAuditEntry] = []
        for item in raw:
            if isinstance(item, dict):
                out.append(DecisionAuditEntry(**item))
        return out
