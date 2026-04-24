"""Compliance updates for planned weekly sessions."""

from __future__ import annotations

from .load_tracker import recalculate_weekly_load, update_fatigue_trend
from .state_models import CompletedSession, WeeklyState


class ComplianceTracker:
    def mark_completed(
        self,
        state: WeeklyState,
        date: str,
        module_id: str,
        rpe_1_to_10: int,
        duration_min: int,
        notes: str = "",
    ) -> WeeklyState:
        entry = CompletedSession(
            date=date,
            module_id=module_id,
            status="completed",
            rpe_1_to_10=rpe_1_to_10,
            duration_min=duration_min,
            notes=notes,
        )
        state.completed_sessions.append(entry)
        recalculate_weekly_load(state)
        update_fatigue_trend(state)
        return state

    def mark_skipped(self, state: WeeklyState, date: str, module_id: str, notes: str = "") -> WeeklyState:
        entry = CompletedSession(
            date=date,
            module_id=module_id,
            status="skipped",
            rpe_1_to_10=1,
            duration_min=0,
            notes=notes,
        )
        state.skipped_sessions.append(entry)
        state.completed_sessions.append(entry)
        recalculate_weekly_load(state)
        update_fatigue_trend(state)
        return state

    def mark_modified(
        self,
        state: WeeklyState,
        date: str,
        module_id: str,
        rpe_1_to_10: int,
        duration_min: int,
        notes: str = "",
    ) -> WeeklyState:
        entry = CompletedSession(
            date=date,
            module_id=module_id,
            status="modified",
            rpe_1_to_10=rpe_1_to_10,
            duration_min=duration_min,
            notes=notes,
        )
        state.modified_sessions.append(entry)
        state.completed_sessions.append(entry)
        recalculate_weekly_load(state)
        update_fatigue_trend(state)
        return state
