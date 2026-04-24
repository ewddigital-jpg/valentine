"""Simple JSON persistence for weekly planner state."""

from __future__ import annotations

from pathlib import Path
import json

from .state_models import WeeklyState


class StateStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_week(self, state: WeeklyState) -> None:
        all_data = self._read_all()
        all_data[state.week_start] = state.to_dict()
        self.file_path.write_text(json.dumps(all_data, indent=2), encoding="utf-8")

    def load_week(self, week_start: str) -> WeeklyState | None:
        all_data = self._read_all()
        raw = all_data.get(week_start)
        if raw is None:
            return None
        return WeeklyState.from_dict(raw)

    def _read_all(self) -> dict[str, dict[str, object]]:
        if not self.file_path.exists():
            return {}
        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
