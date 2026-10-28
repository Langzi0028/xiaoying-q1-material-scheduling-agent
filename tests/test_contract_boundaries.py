from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


def test_project_contains_no_publish_callable_or_published_status() -> None:
    source_files = [
        path
        for path in (PROJECT_ROOT / "material_scheduler").rglob("*.py")
        if path.name != "prompts.py"
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)

    assert "def publish(" not in source
    assert '"published"' not in source
    assert "'published'" not in source


def test_persisted_draft_schema_is_draft_only() -> None:
    schema = (PROJECT_ROOT / "material_scheduler" / "storage" / "database.py").read_text(encoding="utf-8")

    assert "CHECK (status = 'draft')" in schema
    assert "UNIQUE (schedule_scope, scheduled_time)" in schema
    assert "idempotency_key TEXT NOT NULL UNIQUE" in schema
