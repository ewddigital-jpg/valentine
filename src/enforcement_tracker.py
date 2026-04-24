"""Track compliance with enforced rules and escalate repeated violations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


VALID_STATUSES = {"compliant", "partial", "violated", "skipped", "unknown"}
VALID_PROTEIN_STATUS = {"yes", "partial", "no", "unknown"}
VALID_MEAL_STATUS = {"yes", "partial", "no", "unknown"}
VALID_SNACK_CONTROL = {"none", "controlled", "chaotic"}


@dataclass(frozen=True)
class EnforcementRecord:
    date: str
    structured_meals_status: str
    hydration_status: str
    blocked_actions_status: str
    training_completion_status: str
    skipped_sessions: int
    modified_sessions: int
    notes: str
    estimated_protein_g: int | None = None
    protein_target_hit: str = "unknown"
    meals_followed: str = "unknown"
    snack_control: str = "none"
    missed_meals_count: int = 0
    hunger_level_1_to_5: int | None = None
    notes_about_food: str = ""


@dataclass(frozen=True)
class EscalationResult:
    escalation_flag: bool
    escalation_level: str
    escalation_actions: list[str]
    reasons: list[str]


class EnforcementTracker:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def add_record(self, record: EnforcementRecord) -> None:
        self._validate_record(record)
        records = self.load_records()
        records.append(record)
        self.file_path.write_text(
            json.dumps([asdict(item) for item in records], indent=2), encoding="utf-8"
        )

    def load_records(self) -> list[EnforcementRecord]:
        if not self.file_path.exists():
            return []
        raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        out: list[EnforcementRecord] = []
        for item in raw:
            if isinstance(item, dict):
                out.append(EnforcementRecord(**item))
        return out

    def assess_escalation(self, recent_days: int = 7) -> EscalationResult:
        records = self.load_records()[-recent_days:]
        if not records:
            return EscalationResult(False, "none", [], ["No recent compliance data."])

        reasons: list[str] = []
        actions: list[str] = []

        binge_like_violations = sum(
            1
            for r in records
            if r.structured_meals_status == "violated" and "binge" in r.notes.lower()
        )
        blocked_ignored = sum(1 for r in records if r.blocked_actions_status == "violated")
        undereating_fightcamp = sum(
            1
            for r in records
            if (r.protein_target_hit in {"no", "partial"} or r.missed_meals_count >= 2)
            and "fight_week" in r.notes.lower()
        )
        recovery_missed = sum(
            1
            for r in records
            if r.training_completion_status in {"violated", "skipped"}
            and "recovery" in r.notes.lower()
        )
        binge_pattern = sum(
            1
            for r in records
            if r.meals_followed == "no" and r.snack_control == "chaotic"
        )
        satiety_gap = sum(
            1
            for r in records
            if (r.hunger_level_1_to_5 or 0) >= 4 and r.protein_target_hit in {"no", "partial"}
        )

        if binge_like_violations >= 2:
            reasons.append("Repeated binge-risk + skipped structure detected.")
            actions.append("Enforce fixed 4-feed meal structure for next 3 days.")
        if blocked_ignored >= 2:
            reasons.append("Blocked actions repeatedly ignored.")
            actions.append("Restrict snack environment and lock preplanned menu.")
        if undereating_fightcamp >= 2:
            reasons.append("Repeated under-eating during fight camp markers.")
            actions.append("Force simplified carb+protein feedings every 4 hours.")
        if recovery_missed >= 2:
            reasons.append("Recovery directives repeatedly missed.")
            actions.append("Reduce training complexity to technical/recovery sessions only.")
        if binge_pattern >= 2:
            reasons.append("Meal structure failures with chaotic snacking repeated.")
            actions.append("Apply 3-day anti-binge meal structure intervention.")
        if satiety_gap >= 2:
            reasons.append("High hunger with poor protein adherence repeated.")
            actions.append("Increase satiety-focused meal structure and protein-first feedings.")

        if not reasons:
            return EscalationResult(False, "none", [], ["No escalation trigger threshold met."])

        level = "moderate"
        if len(reasons) >= 3:
            level = "high"
            actions.append("Escalation warning flag: coach review required.")

        return EscalationResult(True, level, _dedupe(actions), reasons)

    def _validate_record(self, record: EnforcementRecord) -> None:
        for value in (
            record.structured_meals_status,
            record.hydration_status,
            record.blocked_actions_status,
            record.training_completion_status,
        ):
            if value not in VALID_STATUSES:
                raise ValueError(f"Invalid enforcement status: {value}")
        if record.protein_target_hit not in VALID_PROTEIN_STATUS:
            raise ValueError(f"Invalid protein_target_hit: {record.protein_target_hit}")
        if record.meals_followed not in VALID_MEAL_STATUS:
            raise ValueError(f"Invalid meals_followed: {record.meals_followed}")
        if record.snack_control not in VALID_SNACK_CONTROL:
            raise ValueError(f"Invalid snack_control: {record.snack_control}")


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out
