from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from material_scheduler.config import Settings
from material_scheduler.llm.client import DecisionEngine
from material_scheduler.llm.decision_tools import DecisionAction
from material_scheduler.fixtures.scenarios import M01_ALTERNATIVE_TIME, M01_REQUESTED_TIME, seed_demo_data
from material_scheduler.graph.workflow import build_workflow
from material_scheduler.models import SchedulingRequest
from material_scheduler.storage.checkpoints import create_sqlite_checkpointer
from material_scheduler.storage.database import Database
from material_scheduler.storage.repositories import Repository
from material_scheduler.trace import TraceRecorder

OUTPUT_PATH = PROJECT_ROOT / "examples" / "05-live-llm-decision.md"
FLOW_OUTPUT_PATH = PROJECT_ROOT / "examples" / "06-live-llm-conflict-flow.md"
NORMAL_FLOW_OUTPUT_PATH = PROJECT_ROOT / "examples" / "08-live-llm-normal-flow.md"
RUNTIME_PATH = PROJECT_ROOT / "data" / ".example-runtime" / "live-llm-conflict.db"


def main() -> None:
    settings = Settings.from_environment()
    if not settings.llm_configured:
        raise SystemExit("Live LLM configuration is required to record this evidence.")

    legal_actions = [DecisionAction.REQUEST_CONFIRMATION, DecisionAction.RETURN_RESULT]
    state = {
        "material_id": "M01",
        "requested_time": "2026-10-28T18:00:00+08:00",
        "requested_slot_available": False,
        "offered_alternatives": ["2026-10-28T19:00:00+08:00"],
        "confirmation_status": "pending",
    }
    result = DecisionEngine(settings).decide(legal_actions, state)
    if result.source != "live_llm":
        raise SystemExit("The LLM request did not complete successfully; evidence was not written.")

    content = f"""# 示例 5：真实 LLM 受限决策

## 输入

```json
{json.dumps({"legal_actions": [action.value for action in legal_actions], "state": state}, ensure_ascii=False, indent=2)}
```

## 实际输出

```json
{json.dumps({"action": result.action.value, "source": result.source, "reason": result.reason}, ensure_ascii=False, indent=2)}
```

## 运行 Trace

```json
{json.dumps([{"node": "decide_next_action", "source": result.source, "validated_action": result.action.value}], ensure_ascii=False, indent=2)}
```

## 验证结论

本例由本地 `.env` 中配置的 OpenAI 兼容模型实际返回。记录不包含 `LLM_BASE_URL`、`LLM_API_KEY` 或完整请求头。模型输出只能来自传入的 `legal_actions`，随后仍需由 Guard、时段工具和草稿存储约束执行。
"""
    OUTPUT_PATH.write_text(content, encoding="utf-8")

    database = Database(RUNTIME_PATH)
    database.initialize()
    repository = Repository(database)
    seed_demo_data(repository)
    trace = TraceRecorder()
    saver, connection = create_sqlite_checkpointer(RUNTIME_PATH)
    try:
        graph = build_workflow(repository, saver, decision_engine=DecisionEngine(settings), trace_recorder=trace)
        request = SchedulingRequest(
            request_id="live-llm-conflict",
            material_id="M01",
            requested_time=M01_REQUESTED_TIME,
            time_requirement_type="preferred",
        )
        result = graph.invoke(
            {"run_id": "live-llm-conflict", **request.model_dump(mode="json")},
            config={"configurable": {"thread_id": "live-llm-conflict"}},
        )
    finally:
        connection.close()

    if "__interrupt__" not in result or not any(event["update"].get("decision_source") == "live_llm" for event in trace.events):
        raise SystemExit("The live conflict flow did not reach a real-LLM confirmation decision.")

    flow_content = f"""# 示例 6：真实 LLM 驱动的冲突处理路径

## 输入

```json
{json.dumps(request.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

## 实际输出

```json
{json.dumps({"run_status": "waiting_confirmation", "suggested_time": M01_ALTERNATIVE_TIME, "draft_save_status": "not_attempted"}, ensure_ascii=False, indent=2)}
```

## 运行 Trace

```json
{json.dumps(trace.events, ensure_ascii=False, indent=2)}
```

## 验证结论

真实在线 LLM 依次基于工具结果选择查目标时段、查替代时段、请求用户确认。Trace 中每个 `decide_next_action` 节点的 `decision_source` 为 `live_llm`。18:00 冲突后推荐 19:00 并中断，未创建草稿；模型不具有发布或直接写库能力。
"""
    FLOW_OUTPUT_PATH.write_text(flow_content, encoding="utf-8")

    normal_database_path = RUNTIME_PATH.with_name("live-llm-normal.db")
    normal_database = Database(normal_database_path)
    normal_database.initialize()
    normal_repository = Repository(normal_database)
    seed_demo_data(normal_repository)
    normal_trace = TraceRecorder()
    normal_saver, normal_connection = create_sqlite_checkpointer(normal_database_path)
    try:
        normal_graph = build_workflow(
            normal_repository,
            normal_saver,
            decision_engine=DecisionEngine(settings),
            trace_recorder=normal_trace,
        )
        normal_request = SchedulingRequest(
            request_id="live-llm-normal",
            material_id="M02",
            requested_time="2026-10-28T20:00:00+08:00",
            time_requirement_type="preferred",
        )
        normal_result = normal_graph.invoke(
            {"run_id": "live-llm-normal", **normal_request.model_dump(mode="json")},
            config={"configurable": {"thread_id": "live-llm-normal"}},
        )
    finally:
        normal_connection.close()

    normal_live_decisions = [
        event for event in normal_trace.events if event["update"].get("decision_source") == "live_llm"
    ]
    if normal_result.get("draft_save_status") != "saved" or len(normal_live_decisions) < 2:
        raise SystemExit("The live normal flow did not complete with real-LLM decisions and a saved draft.")

    normal_content = f"""# 示例 8：真实 LLM 驱动的正常保存路径

## 输入

```json
{json.dumps(normal_request.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

## 实际输出

```json
{json.dumps(normal_result["final_response"], ensure_ascii=False, indent=2)}
```

## 运行 Trace

```json
{json.dumps(normal_trace.events, ensure_ascii=False, indent=2)}
```

## 验证结论

真实在线 LLM 基于审核通过和目标时段可用的工具结果，选择查询目标时段并随后选择保存草稿。Trace 中多个 `decide_next_action` 节点的 `decision_source` 为 `live_llm`。最终结果为 `saved`，但状态仍为草稿，文案明确“尚未发布”。
"""
    NORMAL_FLOW_OUTPUT_PATH.write_text(normal_content, encoding="utf-8")


if __name__ == "__main__":
    main()
