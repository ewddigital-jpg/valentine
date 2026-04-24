from __future__ import annotations

from pathlib import Path

from src.cli import CoachCLI


class InputFeeder:
    def __init__(self, values: list[str]) -> None:
        self.values = values
        self.index = 0

    def __call__(self, _prompt: str = "") -> str:
        if self.index >= len(self.values):
            return ""
        value = self.values[self.index]
        self.index += 1
        return value


def test_command_routing_unknown(tmp_path: Path) -> None:
    cli = CoachCLI(tmp_path, input_fn=InputFeeder([]))
    out = cli.run("unknown")
    assert "Unknown command" in out


def test_checkin_persistence_and_today(tmp_path: Path) -> None:
    feeder = InputFeeder([
        "72.0", "7.0", "2", "2", "4", "3", "3", "", "20", "70", "n", "note",
        "60", "home", "none", "n",
    ])
    cli = CoachCLI(tmp_path, input_fn=feeder)
    out = cli.run("checkin")
    assert "Check-in Saved" in out
    assert (tmp_path / "today_plan.json").exists()

    out_today = cli.run("today")
    assert "Today Plan" in out_today


def test_today_without_existing_plan(tmp_path: Path) -> None:
    cli = CoachCLI(tmp_path, input_fn=InputFeeder([]))
    out = cli.run("today")
    assert "Run checkin first" in out


def test_complete_updates_state(tmp_path: Path) -> None:
    feeder = InputFeeder([
        "72.0", "7.0", "2", "2", "4", "3", "3", "", "20", "70", "n", "note",
        "60", "home", "none", "n",
        "55", "7", "good", "compliant", "compliant",
        "120", "partial", "partial", "controlled", "1", "4", "late lunch",
    ])
    cli = CoachCLI(tmp_path, input_fn=feeder)
    cli.run("checkin")
    out = cli.run("complete")
    assert "completed" in out.lower()
    assert "protein_target_hit: partial" in out
    assert (tmp_path / "weekly_state.json").exists()


def test_skip_updates_state(tmp_path: Path) -> None:
    feeder = InputFeeder([
        "72.0", "7.0", "2", "2", "4", "3", "3", "", "20", "70", "n", "note",
        "60", "home", "none", "n",
        "work conflict",
    ])
    cli = CoachCLI(tmp_path, input_fn=feeder)
    cli.run("checkin")
    out = cli.run("skip")
    assert "skipped" in out.lower()


def test_weight_output_shape(tmp_path: Path) -> None:
    feeder = InputFeeder([
        "72.0", "7.0", "2", "2", "4", "3", "3", "", "20", "70", "n", "note",
        "60", "home", "none", "n",
        "14", "70",
    ])
    cli = CoachCLI(tmp_path, input_fn=feeder)
    cli.run("checkin")
    out = cli.run("weight")
    assert "trend_kg_per_week" in out
    assert "status:" in out


def test_report_output_shape(tmp_path: Path) -> None:
    feeder = InputFeeder([
        "72.0", "7.0", "2", "2", "4", "3", "3", "", "20", "70", "n", "note",
        "60", "home", "none", "n",
    ])
    cli = CoachCLI(tmp_path, input_fn=feeder)
    cli.run("checkin")
    out = cli.run("report")
    assert "active_interventions" in out
    assert "repeated_violation_patterns" in out
