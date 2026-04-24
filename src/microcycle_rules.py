"""Deterministic weekly sequencing rules for module distribution."""

from __future__ import annotations

from dataclasses import dataclass

HIGH_FATIGUE_MODULES = {"strength_day_lower", "boxing_conditioning_day"}
TECHNIQUE_MODULES = {"technical_day", "fight_week_sharpening_day"}
RECOVERY_SUPPORT_MODULES = {"active_recovery_day", "aerobic_base_day", "post_fight_recovery_day"}


@dataclass(frozen=True)
class WeekRuleConfig:
    days_to_fight: int

    @property
    def high_fatigue_cap(self) -> int:
        if self.days_to_fight <= 7:
            return 1
        if self.days_to_fight <= 14:
            return 2
        return 3

    @property
    def sharpening_bias(self) -> bool:
        return self.days_to_fight <= 7


def module_priority(module_id: str, days_to_fight: int, day_idx: int) -> str:
    if day_idx == 6:
        return "optional"
    if days_to_fight <= 7:
        if module_id in {"fight_week_sharpening_day", "technical_day"}:
            return "high"
        if module_id in RECOVERY_SUPPORT_MODULES:
            return "medium"
        return "optional"
    if module_id in HIGH_FATIGUE_MODULES:
        return "high"
    if module_id in {"explosive_day", "technical_day"}:
        return "high"
    if module_id in RECOVERY_SUPPORT_MODULES:
        return "medium"
    return "medium"


def violates_spacing(prev_module: str | None, current_module: str) -> bool:
    if prev_module is None:
        return False
    if prev_module == "strength_day_lower" and current_module in {"boxing_conditioning_day", "explosive_day"}:
        return True
    if prev_module in HIGH_FATIGUE_MODULES and current_module in HIGH_FATIGUE_MODULES:
        return True
    return False
