from typer.testing import CliRunner

from material_scheduler.cli import app


def test_cli_exposes_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "schedule" in result.stdout


def test_schedule_exposes_execution_limit_option() -> None:
    result = CliRunner().invoke(app, ["schedule", "--help"])

    assert result.exit_code == 0
    assert "--max-steps" in result.stdout
