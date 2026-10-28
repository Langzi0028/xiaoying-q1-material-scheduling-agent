from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from langgraph.types import Command

PROJECT_ROOT = Path(__file__).parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from material_scheduler.enums import TimeRequirementType
from material_scheduler.fixtures.scenarios import M01_ALTERNATIVE_TIME, M01_REQUESTED_TIME, seed_demo_data
from material_scheduler.graph.workflow import build_workflow
from material_scheduler.models import SchedulingRequest
from material_scheduler.presentation import format_result
from material_scheduler.storage.checkpoints import create_sqlite_checkpointer
from material_scheduler.storage.database import Database
from material_scheduler.storage.repositories import Repository
from material_scheduler.trace import TraceRecorder

EXAMPLES = PROJECT_ROOT / "examples"
RUNTIME = PROJECT_ROOT / "data" / ".example-runtime"


def make_request(material_id: str, requested_time: str, requirement: TimeRequirementType = TimeRequirementType.PREFERRED) -> SchedulingRequest:
    return SchedulingRequest(
        request_id=f"evidence-{material_id}-{requested_time}",
        material_id=material_id,
        requested_time=requested_time,
        time_requirement_type=requirement,
        schedule_scope="main",
    )


def run_graph(name: str, request: SchedulingRequest, *, resume: dict | None = None, fail_save: bool = False) -> tuple[dict, list[dict]]:
    database_path = RUNTIME / f"{name}.db"
    database = Database(database_path)
    database.initialize()
    repository = Repository(database)
    seed_demo_data(repository)
    recorder = TraceRecorder()
    saver, connection = create_sqlite_checkpointer(database_path)
    run_id = f"example-{name}"
    config = {"configurable": {"thread_id": run_id}}
    try:
        class DeterministicDecisionEngine:
            def choose(self, legal_actions, state):
                return legal_actions[0]

        graph = build_workflow(
            repository,
            saver,
            fail_save=fail_save,
            trace_recorder=recorder,
            decision_engine=DeterministicDecisionEngine(),
        )
        state = {"run_id": run_id, **request.model_dump(mode="json")}
        result = graph.invoke(state, config=config)
        if resume is not None:
            result = graph.invoke(Command(resume=resume), config=config)
        return result, recorder.events
    finally:
        connection.close()


def write_example(filename: str, title: str, request: dict, result: dict, trace: list[dict], notes: str) -> None:
    content = f"""# {title}

## 输入

```json
{json.dumps(request, ensure_ascii=False, indent=2)}
```

## 实际输出

```json
{format_result(result)}
```

## 运行 Trace

```json
{json.dumps(trace, ensure_ascii=False, indent=2)}
```

## 验证结论

{notes}
"""
    (EXAMPLES / filename).write_text(content, encoding="utf-8")


def main() -> None:
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)

    normal_request = make_request("M02", "2026-10-28T20:00:00+08:00")
    normal_result, normal_trace = run_graph("normal", normal_request)
    write_example(
        "01-normal-success.md",
        "示例 1：正常排期并保存草稿",
        normal_request.model_dump(mode="json"),
        normal_result,
        normal_trace,
        "审核通过、目标时段可用，保存状态为 `saved`。输出明确为草稿且“尚未发布”。",
    )

    missing_request = make_request("M03", "2026-10-28T20:00:00+08:00")
    missing_result, missing_trace = run_graph("missing-info", missing_request)
    write_example(
        "02-missing-info.md",
        "示例 2：素材信息不足",
        missing_request.model_dump(mode="json"),
        missing_result,
        missing_trace,
        "审核状态为 `needs_info`，指出缺失 `copyright_status`，草稿保存状态为 `not_attempted`。",
    )

    conflict_request = make_request("M01", M01_REQUESTED_TIME)
    database_path = RUNTIME / "conflict-confirm.db"
    database = Database(database_path)
    database.initialize()
    repository = Repository(database)
    seed_demo_data(repository)
    recorder = TraceRecorder()
    saver, connection = create_sqlite_checkpointer(database_path)
    conflict_config = {"configurable": {"thread_id": "example-conflict-confirm"}}
    try:
        class DeterministicDecisionEngine:
            def choose(self, legal_actions, state):
                return legal_actions[0]

        graph = build_workflow(repository, saver, decision_engine=DeterministicDecisionEngine(), trace_recorder=recorder)
        conflict_initial = graph.invoke(
            {"run_id": "example-conflict-confirm", **conflict_request.model_dump(mode="json")},
            config=conflict_config,
        )
        conflict_result = graph.invoke(
            Command(resume={"confirmed": True, "selected_time": M01_ALTERNATIVE_TIME}),
            config=conflict_config,
        )
        duplicate_result = graph.invoke(
            {"run_id": "example-conflict-duplicate", **conflict_request.model_dump(mode="json")},
            config={"configurable": {"thread_id": "example-conflict-duplicate"}},
        )
        conflict_trace = recorder.events
    finally:
        connection.close()
    write_example(
        "03-conflict-confirm-duplicate.md",
        "示例 3：冲突调整、用户确认与重复提交",
        conflict_request.model_dump(mode="json"),
        {
            "first_run": json.loads(format_result(conflict_initial)),
            "confirmed_run": json.loads(format_result(conflict_result)),
            "duplicate_run": json.loads(format_result(duplicate_result)),
        },
        conflict_trace,
        "首次运行因 18:00 占用而中断，建议 19:00 并等待确认。确认后只保存草稿。随后以相同请求重新运行，`duplicate_run` 返回 `duplicate_reused`，复用同一草稿。",
    )

    failure_request = make_request("M02", "2026-10-28T22:00:00+08:00")
    failure_result, failure_trace = run_graph("save-failure", failure_request, fail_save=True)
    write_example(
        "04-save-failure.md",
        "示例 4：草稿保存失败",
        failure_request.model_dump(mode="json"),
        failure_result,
        failure_trace,
        "保存工具注入失败，返回 `failed` 和 `SAVE_FAILED`；不会声称草稿已保存或发布成功。",
    )

    limit_request = make_request("M02", "2026-10-28T20:00:00+08:00")
    database_path = RUNTIME / "execution-limit.db"
    database = Database(database_path)
    database.initialize()
    repository = Repository(database)
    seed_demo_data(repository)
    recorder = TraceRecorder()
    saver, connection = create_sqlite_checkpointer(database_path)
    try:
        class DeterministicDecisionEngine:
            def choose(self, legal_actions, state):
                return legal_actions[0]

        graph = build_workflow(repository, saver, decision_engine=DeterministicDecisionEngine(), trace_recorder=recorder)
        limit_result = graph.invoke(
            {
                "run_id": "example-execution-limit",
                "max_steps": 1,
                "execution_steps": 0,
                **limit_request.model_dump(mode="json"),
            },
            config={"configurable": {"thread_id": "example-execution-limit"}},
        )
    finally:
        connection.close()
    write_example(
        "07-execution-limit.md",
        "示例 7：达到执行上限的未完成状态",
        {**limit_request.model_dump(mode="json"), "max_steps": 1},
        limit_result,
        recorder.events,
        "流程达到 `max_steps` 后返回 `execution_status: incomplete` 和 `EXECUTION_LIMIT_REACHED`，未创建草稿。",
    )


if __name__ == "__main__":
    main()
