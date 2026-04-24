"""Weekly load and fatigue trend tracking helpers."""

from __future__ import annotations

from .state_models import WeeklyState


def session_load(duration_min: int, rpe_1_to_10: int) -> float:
    return round((duration_min * rpe_1_to_10) / 10.0, 2)


def recalculate_weekly_load(state: WeeklyState) -> float:
    total = 0.0
    for session in state.completed_sessions:
        if session.status == "completed":
            total += session_load(session.duration_min, session.rpe_1_to_10)
        if session.status == "modified":
            total += session_load(session.duration_min, max(session.rpe_1_to_10 - 1, 1))
    state.weekly_load_score = round(total, 2)
    return state.weekly_load_score


def update_fatigue_trend(state: WeeklyState) -> list[float]:
    if not state.completed_sessions:
        return state.rolling_fatigue_trend
    avg_rpe = sum(item.rpe_1_to_10 for item in state.completed_sessions) / len(state.completed_sessions)
    state.rolling_fatigue_trend.append(round(avg_rpe, 2))
    state.rolling_fatigue_trend = state.rolling_fatigue_trend[-4:]
    return state.rolling_fatigue_trend
