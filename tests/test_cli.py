from pathlib import Path
from uuid import uuid4

from typer.testing import CliRunner

from material_scheduler.cli import app


def _database_path() -> Path:
    root = Path.cwd() / "data" / ".test-runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{uuid4().hex}.db"


def test_normal_demo_reports_saved_draft_and_not_published() -> None:
    result = CliRunner().invoke(app, ["demo", "normal", "--database", str(_database_path())])

    assert result.exit_code == 0, result.stdout
    assert '"draft_save_status": "saved"' in result.stdout
    assert "草稿已保存，尚未发布" in result.stdout
    assert "已发布" not in result.stdout


def test_conflict_demo_waits_for_confirmation_without_creating_draft() -> None:
    result = CliRunner().invoke(app, ["demo", "conflict", "--database", str(_database_path())])

    assert result.exit_code == 0, result.stdout
    assert '"run_status": "waiting_confirmation"' in result.stdout
    assert '"suggested_time": "2026-10-28T19:00:00+08:00"' in result.stdout
    assert '"draft_save_status": "not_attempted"' in result.stdout
    assert "尚未发布" in result.stdout


def test_resume_command_confirms_conflict_and_saves_only_a_draft() -> None:
    database = _database_path()
    runner = CliRunner()
    initial = runner.invoke(app, ["demo", "conflict", "--database", str(database)])
    run_id = next(line.split(": ", 1)[1] for line in initial.stdout.splitlines() if line.startswith("run_id:"))

    resumed = runner.invoke(
        app,
        [
            "resume",
            "--run-id",
            run_id,
            "--confirm",
            "--time",
            "2026-10-28T19:00:00+08:00",
            "--database",
            str(database),
        ],
    )

    assert resumed.exit_code == 0, resumed.stdout
    assert '"draft_save_status": "saved"' in resumed.stdout
    assert "草稿已保存，尚未发布" in resumed.stdout


def test_save_failure_demo_returns_failed_without_false_success() -> None:
    result = CliRunner().invoke(app, ["demo", "save-failure", "--database", str(_database_path())])

    assert result.exit_code == 0, result.stdout
    assert '"draft_save_status": "failed"' in result.stdout
    assert "草稿保存失败" in result.stdout
    assert "草稿已保存" not in result.stdout


def test_unknown_material_cli_returns_structured_error_without_draft() -> None:
    result = CliRunner().invoke(
        app,
        [
            "schedule",
            "--material-id",
            "M99",
            "--time",
            "2026-10-28T20:00:00+08:00",
            "--database",
            str(_database_path()),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert '"error_code": "MATERIAL_NOT_FOUND"' in result.stdout
    assert '"draft_save_status": "not_attempted"' in result.stdout
