from uuid import uuid4

from material_scheduler.enums import DraftSaveStatus
from material_scheduler.graph.workflow import build_workflow
from material_scheduler.models import SchedulingRequest


def test_execution_limit_returns_incomplete_without_creating_draft(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    request = SchedulingRequest(
        request_id=f"limit-{uuid4().hex}",
        material_id="M02",
        requested_time="2026-10-28T20:00:00+08:00",
        time_requirement_type="preferred",
    )
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)

    result = graph.invoke(
        {
            "run_id": "run-execution-limit",
            "max_steps": 1,
            "execution_steps": 0,
            **request.model_dump(mode="json"),
        },
        config={"configurable": {"thread_id": "run-execution-limit"}},
    )

    assert result["final_response"]["execution_status"] == "incomplete"
    assert result["final_response"]["error_code"] == "EXECUTION_LIMIT_REACHED"
    assert result["draft_save_status"] == DraftSaveStatus.NOT_ATTEMPTED.value
    assert repository.count_drafts() == 0
