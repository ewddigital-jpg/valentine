"""Local deterministic CLI for day-to-day coaching workflow."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import json

from .checkin_workflow import CheckinInput, CheckinWorkflow
from .context_models import DailyContext
from .daily_planner import DailyPlanner
from .decision_audit import DecisionAuditEntry, DecisionAuditStore
from .enforcement_tracker import EnforcementRecord, EnforcementTracker
from .exception_reports import build_weekly_exception_report
from .intervention_bridge import InterventionBridge
from .intervention_engine import InterventionEngine
from .intervention_state import InterventionStateStore
from .intervention_tracker import InterventionTracker
from .load_tracker import recalculate_weekly_load
from .state_models import WeeklyState, week_start_from_date
from .state_store import StateStore
from .weekly_planner import WeeklyContext, WeeklyPlanner
from .weight_logic import evaluate_weight_trajectory


class CoachCLI:
    def __init__(self, data_dir: Path, input_fn=input) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.input_fn = input_fn

        self.checkin_workflow = CheckinWorkflow()
        self.daily_planner = DailyPlanner()
        self.weekly_planner = WeeklyPlanner()

        self.decision_store = DecisionAuditStore(self.data_dir / "decisions.json")
        self.enforcement_tracker = EnforcementTracker(self.data_dir / "enforcement.json")
        self.intervention_state_store = InterventionStateStore(self.data_dir / "intervention.json")
        self.intervention_tracker = InterventionTracker(self.intervention_state_store)
        self.intervention_engine = InterventionEngine(self.data_dir / "intervention.json")
        self.bridge = InterventionBridge(
            checkin_workflow=self.checkin_workflow,
            intervention_engine=self.intervention_engine,
            intervention_tracker=self.intervention_tracker,
        )
        self.state_store = StateStore(self.data_dir / "weekly_state.json")

    def run(self, command: str) -> str:
        if command == "checkin":
            return self.cmd_checkin()
        if command == "today":
            return self.cmd_today()
        if command == "week":
            return self.cmd_week()
        if command == "complete":
            return self.cmd_complete()
        if command == "skip":
            return self.cmd_skip()
        if command == "weight":
            return self.cmd_weight()
        if command == "report":
            return self.cmd_report()
        return "Unknown command. Use: checkin|today|week|complete|skip|weight|report"

    def cmd_checkin(self) -> str:
        today = date.today().isoformat()
        payload = self._collect_checkin_inputs()
        checkin = CheckinInput(**payload)

        escalation = self.enforcement_tracker.assess_escalation(recent_days=7)
        output = self.bridge.run_daily_checkin(
            date=today,
            checkin_input=checkin,
            escalation=escalation,
            warning_flags=[],
        )

        daily_context = self._context_from_checkin(checkin)
        daily_plan = self.daily_planner.build_daily_plan(daily_context)

        output["selected_training_module"] = daily_plan["selected_module"]
        output["session_summary"] = daily_plan["session_1"]

        self._save_json(self.data_dir / "today_plan.json", {"date": today, "plan": output})
        self._append_weight(today, checkin.bodyweight_kg)

        audit_entry = DecisionAuditEntry(
            date=today,
            mode=str(output["mode"]),
            selected_training_module=str(output["selected_training_module"]),
            selected_nutrition_module=str(output["nutrition_module_for_day"]),
            weight_status=str(output["weight_status"]),
            enforced_rules=list(output["enforced_rules"]),
            blocked_actions=list(output["blocked_actions"]),
            behavior_adjustments=list(output["behavior_adjustments"]),
            warning_flags=list(output["warning_flags"]),
            rationale=list(output["rationale"]),
        )
        self.decision_store.log_decision(audit_entry)

        return self._format_checkin_output(output)

    def cmd_today(self) -> str:
        data = self._load_json(self.data_dir / "today_plan.json")
        if data is None or data.get("date") != date.today().isoformat():
            return "No plan saved for today. Run checkin first."
        plan = data["plan"]
        return (
            f"Today Plan ({data['date']})\n"
            f"Mode: {plan['mode']}\n"
            f"Training: {plan['selected_training_module']}\n"
            f"Nutrition: {plan['nutrition_module_for_day']}\n"
            f"Protein: {plan['protein_target']} g\n"
            f"Hydration: {plan['hydration_target']} ml"
        )

    def cmd_week(self) -> str:
        today = date.today()
        days_to_fight = int(self._input_or_default("days_to_fight", "14"))
        context = WeeklyContext(
            week_start=today.fromordinal(today.toordinal() - today.weekday()),
            days_to_fight=days_to_fight,
            fixed_boxing_gym_days=[],
            allow_double_sessions=False,
            prior_week_load_score=0.0,
        )
        week_out = self.weekly_planner.generate_weekly_plan(context)
        lines = ["Weekly Plan:"]
        intervention = self.intervention_state_store.load()
        for item in week_out["day_by_day_module_plan"]:
            marker = ""
            if intervention and intervention.active and intervention.start_date <= item["date"] <= intervention.end_date:
                marker = " [INT]"
            lines.append(f"{item['date']} | {item['module_id']} | {item['priority']} | {item['rationale']}{marker}")
        return "\n".join(lines)

    def cmd_complete(self) -> str:
        today_data = self._require_today_plan()
        if isinstance(today_data, str):
            return today_data

        duration = int(self.input_fn("actual duration min: "))
        rpe = int(self.input_fn("session RPE 1-10: "))
        notes = self.input_fn("notes: ")
        structured = self.input_fn("structured_meals_status: ")
        hydration = self.input_fn("hydration_status: ")
        estimated_protein_g = int(self._input_or_default("estimated_protein_g", "0"))
        protein_target_hit = self.input_fn("protein_target_hit (yes/partial/no): ").strip().lower() or "unknown"
        meals_followed = self.input_fn("meals_followed (yes/partial/no): ").strip().lower() or "unknown"
        snack_control = self.input_fn("snack_control (none/controlled/chaotic): ").strip().lower() or "none"
        missed_meals_count = int(self._input_or_default("missed_meals_count", "0"))
        hunger_level = int(self._input_or_default("hunger_level_1_to_5", "3"))
        notes_about_food = self.input_fn("notes_about_food: ")

        today = date.today()
        week_start = week_start_from_date(today)
        state = self.state_store.load_week(week_start) or WeeklyState(week_start=week_start)
        from .compliance_tracker import ComplianceTracker

        ComplianceTracker().mark_completed(
            state,
            today.isoformat(),
            today_data["plan"]["selected_training_module"],
            rpe_1_to_10=max(1, min(10, rpe)),
            duration_min=duration,
            notes=notes,
        )
        recalculate_weekly_load(state)
        self.state_store.save_week(state)

        record = EnforcementRecord(
            date=today.isoformat(),
            structured_meals_status=structured,
            hydration_status=hydration,
            blocked_actions_status="compliant",
            training_completion_status="compliant",
            skipped_sessions=0,
            modified_sessions=0,
            notes=notes,
            estimated_protein_g=estimated_protein_g,
            protein_target_hit=protein_target_hit,
            meals_followed=meals_followed,
            snack_control=snack_control,
            missed_meals_count=missed_meals_count,
            hunger_level_1_to_5=hunger_level,
            notes_about_food=notes_about_food,
        )
        self.enforcement_tracker.add_record(record)
        self.bridge.record_enforcement_update(today.isoformat(), record, self._latest_weight())
        warning_flags: list[str] = []
        if protein_target_hit == "no":
            warning_flags.append("recovery_risk_low_protein")
        if meals_followed == "no" and snack_control == "chaotic":
            warning_flags.append("binge_risk_pattern")
        if missed_meals_count >= 2:
            warning_flags.append("structure_failure")
        if hunger_level >= 4 and protein_target_hit in {"no", "partial"}:
            warning_flags.append("add_satiety_structure_tomorrow")

        return (
            "Session marked completed.\n"
            f"protein_target_hit: {protein_target_hit}\n"
            f"meal_structure_followed: {meals_followed}\n"
            f"warning_flags: {warning_flags}"
        )

    def cmd_skip(self) -> str:
        today_data = self._require_today_plan()
        if isinstance(today_data, str):
            return today_data
        reason = self.input_fn("reason (optional): ")

        today = date.today()
        week_start = week_start_from_date(today)
        state = self.state_store.load_week(week_start) or WeeklyState(week_start=week_start)
        from .compliance_tracker import ComplianceTracker

        ComplianceTracker().mark_skipped(
            state,
            today.isoformat(),
            today_data["plan"]["selected_training_module"],
            notes=reason,
        )
        self.state_store.save_week(state)

        record = EnforcementRecord(
            date=today.isoformat(),
            structured_meals_status="unknown",
            hydration_status="unknown",
            blocked_actions_status="unknown",
            training_completion_status="skipped",
            skipped_sessions=1,
            modified_sessions=0,
            notes=reason,
        )
        self.enforcement_tracker.add_record(record)
        self.bridge.record_enforcement_update(today.isoformat(), record, self._latest_weight())
        return "Session marked skipped."

    def cmd_weight(self) -> str:
        weights = self._load_json(self.data_dir / "weights.json") or []
        recent = [float(x["weight"]) for x in weights[-7:]]
        if not recent:
            return "No weight data yet. Run checkin first."
        current = recent[-1]
        days_to_fight = int(self._input_or_default("days_to_fight", "14"))
        target = float(self._input_or_default("fight_weight_target", str(round(current - 2.0, 1))))

        result = evaluate_weight_trajectory(current, target, days_to_fight, recent)
        mode = "unknown"
        today_data = self._load_json(self.data_dir / "today_plan.json")
        if today_data and today_data.get("plan"):
            mode = today_data["plan"].get("mode", "unknown")

        return (
            "Weight Summary\n"
            f"trend_kg_per_week: {result.trend_kg_per_week}\n"
            f"projected_fight_weight: {result.projected_weight_at_fight}\n"
            f"status: {result.status_flag}\n"
            f"action_priorities: {', '.join(result.action_priorities)}\n"
            f"mode: {mode}"
        )

    def cmd_report(self) -> str:
        decisions = self.decision_store.load_all()
        enforcement = self.enforcement_tracker.load_records()
        active = self.intervention_state_store.load()
        interventions = [active] if active else []
        report = build_weekly_exception_report(decisions, enforcement, interventions)
        return (
            "Weekly Report\n"
            f"active_interventions: {report['active_interventions_this_week']}\n"
            f"intervention_outcomes: {report['intervention_outcomes']}\n"
            f"repeated_violation_patterns: {report['repeated_violation_patterns']}\n"
            f"rules_triggered_most_often: {report['rules_triggered_most_often']}\n"
            f"recommendations_ignored_most_often: {report['recommendations_ignored_most_often']}"
        )

    def _collect_checkin_inputs(self) -> dict[str, object]:
        return {
            "bodyweight_kg": float(self.input_fn("bodyweight: ")),
            "sleep_hours": float(self.input_fn("sleep: ")),
            "fatigue_1_to_5": int(self.input_fn("fatigue 1-5: ")),
            "soreness_1_to_5": int(self.input_fn("soreness 1-5: ")),
            "energy_1_to_5": int(self.input_fn("energy 1-5: ")),
            "stress_1_to_5": int(self.input_fn("stress 1-5: ")),
            "hunger_1_to_5": int(self.input_fn("hunger 1-5: ")),
            "binge_risk_note": self.input_fn("binge_risk (text): "),
            "days_to_fight": int(self.input_fn("days_to_fight: ")),
            "todays_training_plan_module": "technical_day",
            "yesterday_completion_status": "completed",
            "recent_bodyweights": self._recent_weights_or_default(),
            "fight_weight_target_kg": float(self._input_or_default("fight_weight_target", "70")),
            "double_session_today": self._as_bool(self.input_fn("double_session_today (y/n): ")),
            "adherence_missed_meals": 0,
            "low_appetite_flag": False,
            "plateau_days": 0,
            "workday_limited_prep": False,
            "notes": self.input_fn("notes: "),
        }

    def _context_from_checkin(self, checkin: CheckinInput) -> DailyContext:
        return DailyContext(
            date=date.today(),
            bodyweight_kg=checkin.bodyweight_kg,
            sleep_hours=checkin.sleep_hours,
            fatigue_1_to_5=checkin.fatigue_1_to_5,
            soreness_upper_1_to_5=checkin.soreness_1_to_5,
            soreness_lower_1_to_5=checkin.soreness_1_to_5,
            energy_1_to_5=checkin.energy_1_to_5,
            stress_1_to_5=checkin.stress_1_to_5,
            motivation_1_to_5=3,
            days_to_fight=checkin.days_to_fight,
            last_session_module="technical_day",
            last_session_intensity=3,
            yesterday_had_run=False,
            yesterday_had_sprints=False,
            yesterday_had_sparring=False,
            weekly_load_score=15,
            time_available_min=int(self._input_or_default("time_available_min", "60")),
            location_today=self._input_or_default("location_today", "home"),
            equipment_today=[x.strip() for x in self._input_or_default("equipment_today comma", "none").split(",") if x.strip()],
            double_session_today=checkin.double_session_today,
            boxing_gym_session_fixed=self._as_bool(self._input_or_default("boxing_gym_session_fixed y/n", "n")),
            notes=checkin.notes,
        )

    def _save_json(self, path: Path, data: object) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_json(self, path: Path) -> object | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _append_weight(self, day: str, weight: float) -> None:
        path = self.data_dir / "weights.json"
        data = self._load_json(path) or []
        if isinstance(data, list):
            data.append({"date": day, "weight": weight})
            self._save_json(path, data)

    def _recent_weights_or_default(self) -> list[float]:
        data = self._load_json(self.data_dir / "weights.json")
        if isinstance(data, list) and data:
            return [float(x["weight"]) for x in data[-7:]]
        return [72.0, 72.0, 72.0]

    def _latest_weight(self) -> float:
        data = self._load_json(self.data_dir / "weights.json")
        if isinstance(data, list) and data:
            return float(data[-1]["weight"])
        return 72.0

    def _require_today_plan(self) -> dict[str, object] | str:
        data = self._load_json(self.data_dir / "today_plan.json")
        if data is None or data.get("date") != date.today().isoformat():
            return "No plan saved for today. Run checkin first."
        return data

    def _format_checkin_output(self, output: dict[str, object]) -> str:
        return (
            "Check-in Saved\n"
            f"mode: {output['mode']}\n"
            f"training recommendation: {output['training_recommendation']}\n"
            f"selected training module: {output['selected_training_module']}\n"
            f"session summary main block: {output['session_summary']['main_block']}\n"
            f"nutrition module: {output['nutrition_module_for_day']}\n"
            f"protein target: {output['protein_target']}\n"
            f"hydration target: {output['hydration_target']}\n"
            f"meal timing focus: {output['meal_timing_focus']}\n"
            f"warning flags: {output['warning_flags']}\n"
            f"enforced rules: {output['enforced_rules']}\n"
            f"blocked actions: {output['blocked_actions']}\n"
            f"active intervention: {output['active_intervention']}\n"
            f"meal examples: {output['example_meals']}"
        )

    def _as_bool(self, text: str) -> bool:
        return text.strip().lower() in {"y", "yes", "true", "1"}

    def _input_or_default(self, label: str, default: str) -> str:
        value = self.input_fn(f"{label} [{default}]: ").strip()
        return value if value else default


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = argv or sys.argv[1:]
    command = argv[0] if argv else ""
    cli = CoachCLI(Path(".coach_data"))
    print(cli.run(command))
    return 0
