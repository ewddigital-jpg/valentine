"""Persistent state models for weekly planning and compliance tracking."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime


@dataclass
class PlannedSession:
    date: str
    module_id: str
    rationale: str
    priority: str
    double_session: bool = False


@dataclass
class CompletedSession:
    date: str
    module_id: str
    status: str  # completed | skipped | modified
    rpe_1_to_10: int
    duration_min: int
    notes: str = ""


@dataclass
class WeeklyState:
    week_start: str
    planned_sessions: list[PlannedSession] = field(default_factory=list)
    completed_sessions: list[CompletedSession] = field(default_factory=list)
    skipped_sessions: list[CompletedSession] = field(default_factory=list)
    modified_sessions: list[CompletedSession] = field(default_factory=list)
    bodyweight_trend_kg: list[float] = field(default_factory=list)
    weekly_load_score: float = 0.0
    rolling_fatigue_trend: list[float] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "week_start": self.week_start,
            "planned_sessions": [asdict(item) for item in self.planned_sessions],
            "completed_sessions": [asdict(item) for item in self.completed_sessions],
            "skipped_sessions": [asdict(item) for item in self.skipped_sessions],
            "modified_sessions": [asdict(item) for item in self.modified_sessions],
            "bodyweight_trend_kg": self.bodyweight_trend_kg,
            "weekly_load_score": self.weekly_load_score,
            "rolling_fatigue_trend": self.rolling_fatigue_trend,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "WeeklyState":
        return cls(
            week_start=str(data["week_start"]),
            planned_sessions=[PlannedSession(**item) for item in data.get("planned_sessions", [])],
            completed_sessions=[CompletedSession(**item) for item in data.get("completed_sessions", [])],
            skipped_sessions=[CompletedSession(**item) for item in data.get("skipped_sessions", [])],
            modified_sessions=[CompletedSession(**item) for item in data.get("modified_sessions", [])],
            bodyweight_trend_kg=[float(x) for x in data.get("bodyweight_trend_kg", [])],
            weekly_load_score=float(data.get("weekly_load_score", 0.0)),
            rolling_fatigue_trend=[float(x) for x in data.get("rolling_fatigue_trend", [])],
            notes=[str(x) for x in data.get("notes", [])],
        )


def week_start_from_date(day: date) -> str:
    monday = day.fromordinal(day.toordinal() - day.weekday())
    return monday.isoformat()


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
