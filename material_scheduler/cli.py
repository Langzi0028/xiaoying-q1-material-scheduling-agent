from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

import typer
from langgraph.types import Command

from .config import Settings
from .enums import RunStatus, TimeRequirementType
from .fixtures.scenarios import M01_ALTERNATIVE_TIME, M01_REQUESTED_TIME, seed_demo_data
from .graph.workflow import build_workflow
from .models import SchedulingRequest
from .presentation import format_result
from .storage.checkpoints import create_sqlite_checkpointer
from .storage.database import Database
from .storage.repositories import Repository

app = typer.Typer(no_args_is_help=True, help="素材审核与发布排期草稿 Agent。仅保存草稿，绝不发布。")


def _open_runtime(database_path: Path, *, fail_save: bool = False):
    database = Database(database_path)
    database.initialize()
    repository = Repository(database)
    checkpointer, connection = create_sqlite_checkpointer(database_path)
    graph = build_workflow(repository, checkpointer, fail_save=fail_save)
    return repository, graph, connection


def _run_request(
    request: SchedulingRequest,
    database_path: Path,
    *,
    fail_save: bool = False,
    run_id: str | None = None,
    max_steps: int = 24,
) -> tuple[str, dict]:
    run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
    repository, graph, connection = _open_runtime(database_path, fail_save=fail_save)
    try:
        repository.create_run(run_id, request)
        initial_state = {
            "run_id": run_id,
            "max_steps": max_steps,
            "execution_steps": 0,
            **request.model_dump(mode="json"),
        }
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": run_id}})
        if "__interrupt__" in result:
            repository.update_run(run_id, RunStatus.WAITING_CONFIRMATION, None)
        else:
            status = RunStatus.FAILED if result.get("draft_save_status") == "failed" else RunStatus.COMPLETED
            repository.update_run(run_id, status, result.get("final_response"))
        return run_id, result
    finally:
        connection.close()


@app.command()
def schedule(
    material_id: Annotated[str, typer.Option("--material-id")],
    time: Annotated[str, typer.Option("--time")],
    requirement: Annotated[TimeRequirementType, typer.Option("--requirement")] = TimeRequirementType.PREFERRED,
    scope: Annotated[str, typer.Option("--scope")] = "main",
    max_steps: Annotated[int, typer.Option("--max-steps", min=1)] = 24,
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Audit a material and create a draft when the workflow permits it."""
    settings = Settings.from_environment()
    request = SchedulingRequest(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        material_id=material_id,
        requested_time=time,
        time_requirement_type=requirement,
        schedule_scope=scope,
    )
    run_id, result = _run_request(request, database or settings.database_path, max_steps=max_steps)
    typer.echo(f"run_id: {run_id}")
    typer.echo(format_result(result))


@app.command()
def resume(
    run_id: Annotated[str, typer.Option("--run-id")],
    confirm: Annotated[bool, typer.Option("--confirm/--reject")] = True,
    time: Annotated[str | None, typer.Option("--time")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Resume an interrupted alternative-slot confirmation."""
    settings = Settings.from_environment()
    database_path = database or settings.database_path
    repository, graph, connection = _open_runtime(database_path)
    try:
        run = repository.get_run(run_id)
        if run is None:
            raise typer.BadParameter(f"未找到运行记录 {run_id}")
        result = graph.invoke(
            Command(resume={"confirmed": confirm, "selected_time": time}),
            config={"configurable": {"thread_id": run_id}},
        )
        if "__interrupt__" in result:
            repository.update_run(run_id, RunStatus.WAITING_CONFIRMATION, None)
        else:
            status = RunStatus.FAILED if result.get("draft_save_status") == "failed" else RunStatus.COMPLETED
            repository.update_run(run_id, status, result.get("final_response"))
        typer.echo(f"run_id: {run_id}")
        typer.echo(format_result(result))
    finally:
        connection.close()


@app.command("show")
def show_run(
    run_id: Annotated[str, typer.Option("--run-id")],
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Show a persisted run summary."""
    settings = Settings.from_environment()
    repository = Repository(Database(database or settings.database_path))
    run = repository.get_run(run_id)
    if run is None:
        raise typer.BadParameter(f"未找到运行记录 {run_id}")
    payload = run.response.model_dump(mode="json") if run.response else {"run_id": run_id, "status": run.status.value}
    typer.echo(format_result({"final_response": payload}))


@app.command("list-runs")
def list_runs(database: Annotated[Path | None, typer.Option("--database")] = None) -> None:
    """List all persisted workflow runs."""
    settings = Settings.from_environment()
    repository = Repository(Database(database or settings.database_path))
    payload = [
        {
            "run_id": run.run_id,
            "material_id": run.request.material_id,
            "status": run.status.value,
            "draft_id": run.response.draft_id if run.response else None,
        }
        for run in repository.list_runs()
    ]
    typer.echo(__import__("json").dumps(payload, ensure_ascii=False, indent=2))


@app.command()
def demo(
    scenario: Annotated[str, typer.Argument(help="seed, normal, conflict, missing-info, rule-risk, duplicate, save-failure")],
    database: Annotated[Path, typer.Option("--database")] = Path("data/demo_material_scheduler.db"),
) -> None:
    """Run deterministic acceptance demonstrations using real SQLite and LangGraph."""
    base_database = Database(database)
    base_database.initialize()
    repository = Repository(base_database)
    seed_demo_data(repository)

    if scenario == "seed":
        typer.echo(f"已写入演示素材和排期数据: {database}")
        return
    if scenario == "normal":
        request = SchedulingRequest(
            request_id="demo-normal",
            material_id="M02",
            requested_time="2026-10-28T20:00:00+08:00",
            time_requirement_type=TimeRequirementType.PREFERRED,
        )
        run_id, result = _run_request(request, database)
    elif scenario == "conflict":
        request = SchedulingRequest(
            request_id="demo-conflict",
            material_id="M01",
            requested_time=M01_REQUESTED_TIME,
            time_requirement_type=TimeRequirementType.PREFERRED,
        )
        run_id, result = _run_request(request, database)
    elif scenario == "missing-info":
        request = SchedulingRequest(
            request_id="demo-missing",
            material_id="M03",
            requested_time="2026-10-28T20:00:00+08:00",
            time_requirement_type=TimeRequirementType.PREFERRED,
        )
        run_id, result = _run_request(request, database)
    elif scenario == "rule-risk":
        request = SchedulingRequest(
            request_id="demo-risk",
            material_id="M04",
            requested_time="2026-10-28T20:00:00+08:00",
            time_requirement_type=TimeRequirementType.PREFERRED,
        )
        run_id, result = _run_request(request, database)
    elif scenario == "duplicate":
        request = SchedulingRequest(
            request_id="demo-duplicate",
            material_id="M02",
            requested_time="2026-10-28T21:00:00+08:00",
            time_requirement_type=TimeRequirementType.PREFERRED,
        )
        _, first = _run_request(request, database)
        run_id, result = _run_request(request, database)
        result["first_draft_id"] = first.get("draft_id")
    elif scenario == "save-failure":
        request = SchedulingRequest(
            request_id="demo-save-failure",
            material_id="M02",
            requested_time="2026-10-28T22:00:00+08:00",
            time_requirement_type=TimeRequirementType.PREFERRED,
        )
        run_id, result = _run_request(request, database, fail_save=True)
    else:
        raise typer.BadParameter(f"不支持的演示场景: {scenario}")
    typer.echo(f"run_id: {run_id}")
    typer.echo(format_result(result))


@app.command("demo-resume")
def demo_resume(
    run_id: Annotated[str, typer.Option("--run-id")],
    database: Annotated[Path, typer.Option("--database")] = Path("data/demo_material_scheduler.db"),
) -> None:
    """Convenience command for confirming the M01 demonstration alternative."""
    resume(run_id=run_id, confirm=True, time=M01_ALTERNATIVE_TIME, database=database)


def main() -> None:
    """Run the command-line interface from the direct project entry point."""
    app()
