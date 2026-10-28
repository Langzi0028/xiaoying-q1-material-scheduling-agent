from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


def test_question_uses_root_entrypoint_and_root_package_layout() -> None:
    assert (PROJECT_ROOT / "main.py").is_file()
    assert (PROJECT_ROOT / "material_scheduler" / "cli.py").is_file()
    assert (PROJECT_ROOT / "requirements.txt").is_file()
    assert not (PROJECT_ROOT / "src").exists()
    assert not (PROJECT_ROOT / "pyproject.toml").exists()


def test_main_entrypoint_only_delegates_to_cli_main() -> None:
    entrypoint = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")

    assert "from material_scheduler.cli import main" in entrypoint
    assert "main()" in entrypoint
