"""Context models for deterministic daily boxing planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


VALID_LOCATIONS = {"home", "park", "gym", "boxing_gym"}


@dataclass(frozen=True)
class DailyContext:
    date: date
    bodyweight_kg: float
    sleep_hours: float
    fatigue_1_to_5: int
    soreness_upper_1_to_5: int
    soreness_lower_1_to_5: int
    energy_1_to_5: int
    stress_1_to_5: int
    motivation_1_to_5: int
    days_to_fight: int
    last_session_module: str
    last_session_intensity: int
    yesterday_had_run: bool
    yesterday_had_sprints: bool
    yesterday_had_sparring: bool
    weekly_load_score: int
    time_available_min: int
    location_today: str
    equipment_today: list[str]
    double_session_today: bool
    boxing_gym_session_fixed: bool
    notes: str

    def __post_init__(self) -> None:
        _assert_range("bodyweight_kg", self.bodyweight_kg, 40.0, 140.0)
        _assert_range("sleep_hours", self.sleep_hours, 0.0, 14.0)
        for name in (
            "fatigue_1_to_5",
            "soreness_upper_1_to_5",
            "soreness_lower_1_to_5",
            "energy_1_to_5",
            "stress_1_to_5",
            "motivation_1_to_5",
            "last_session_intensity",
        ):
            value = getattr(self, name)
            _assert_int_range(name, value, 1, 5)
        if self.days_to_fight < 0:
            raise ValueError("days_to_fight must be >= 0")
        if self.weekly_load_score < 0:
            raise ValueError("weekly_load_score must be >= 0")
        if self.time_available_min < 10:
            raise ValueError("time_available_min must be >= 10")
        if self.location_today not in VALID_LOCATIONS:
            raise ValueError(f"location_today must be one of {sorted(VALID_LOCATIONS)}")

    @property
    def is_sunday(self) -> bool:
        return self.date.weekday() == 6

    @property
    def readiness_score(self) -> float:
        sleep_component = min(self.sleep_hours / 8.0, 1.0) * 2.0
        energy_component = self.energy_1_to_5 * 1.2
        motivation_component = self.motivation_1_to_5 * 0.6
        fatigue_penalty = self.fatigue_1_to_5 * 1.0
        stress_penalty = self.stress_1_to_5 * 0.7
        soreness_penalty = (self.soreness_upper_1_to_5 + self.soreness_lower_1_to_5) * 0.4
        return round(sleep_component + energy_component + motivation_component - fatigue_penalty - stress_penalty - soreness_penalty, 2)


def parse_context_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _assert_int_range(name: str, value: int, low: int, high: int) -> None:
    if not isinstance(value, int) or not (low <= value <= high):
        raise ValueError(f"{name} must be int in range {low}..{high}")


def _assert_range(name: str, value: float, low: float, high: float) -> None:
    if not isinstance(value, (float, int)) or not (low <= float(value) <= high):
        raise ValueError(f"{name} must be in range {low}..{high}")
