from uuid import uuid4

from langgraph.types import Command

from material_scheduler.enums import ConfirmationStatus, DraftSaveStatus, ReviewStatus
from material_scheduler.fixtures.scenarios import M01_ALTERNATIVE_TIME, M01_REQUESTED_TIME
from material_scheduler.graph.workflow import build_workflow
from material_scheduler.models import SchedulingRequest
from material_scheduler.storage.checkpoints import create_sqlite_checkpointer


def _request(material_id: str, requested_time: str, *, requirement: str = "preferred") -> SchedulingRequest:
    return SchedulingRequest(
        request_id=f"req-{uuid4().hex}",
        material_id=material_id,
        requested_time=requested_time,
        time_requirement_type=requirement,
        schedule_scope="main",
    )


def _state(run_id: str, request: SchedulingRequest) -> dict:
    return {"run_id": run_id, **request.model_dump(mode="json")}


def test_normal_available_slot_saves_draft(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M02", "2026-10-28T20:00:00+08:00")
    result = graph.invoke(_state("run-normal", request), config={"configurable": {"thread_id": "run-normal"}})

    assert result["review_status"] == ReviewStatus.APPROVED.value
    assert result["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert result["draft_id"]
    assert "尚未发布" in result["final_response"]["message"]
    assert repository.count_drafts() == 1


def test_missing_metadata_does_not_save_draft(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M03", "2026-10-28T20:00:00+08:00")
    result = graph.invoke(_state("run-missing", request), config={"configurable": {"thread_id": "run-missing"}})

    assert result["review_status"] == ReviewStatus.NEEDS_INFO.value
    assert result["draft_save_status"] == DraftSaveStatus.NOT_ATTEMPTED.value
    assert repository.count_drafts() == 0


def test_rule_risk_blocks_without_saving_draft(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M04", "2026-10-28T20:00:00+08:00")
    result = graph.invoke(_state("run-risk", request), config={"configurable": {"thread_id": "run-risk"}})

    assert result["review_status"] == ReviewStatus.BLOCKED.value
    assert result["risk_reasons"] == ["sensitive_content"]
    assert repository.count_drafts() == 0


def test_m01_conflict_interrupts_until_user_confirms(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M01", M01_REQUESTED_TIME)
    config = {"configurable": {"thread_id": "run-m01"}}
    result = graph.invoke(_state("run-m01", request), config=config)

    assert "__interrupt__" in result
    assert repository.count_drafts() == 0

    resumed = graph.invoke(
        Command(resume={"confirmed": True, "selected_time": M01_ALTERNATIVE_TIME}),
        config=config,
    )
    assert resumed["confirmation_status"] == ConfirmationStatus.CONFIRMED.value
    assert resumed["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert resumed["selected_time"] == M01_ALTERNATIVE_TIME
    assert repository.count_drafts() == 1


def test_hard_time_conflict_waits_for_explicit_confirmation(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M01", M01_REQUESTED_TIME, requirement="hard")
    config = {"configurable": {"thread_id": "run-hard"}}
    result = graph.invoke(_state("run-hard", request), config=config)

    assert "__interrupt__" in result
    assert repository.count_drafts() == 0

    resumed = graph.invoke(
        Command(resume={"confirmed": True, "selected_time": M01_ALTERNATIVE_TIME}),
        config=config,
    )
    assert resumed["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert repository.count_drafts() == 1


def test_duplicate_request_reuses_existing_draft_before_slot_check(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M02", "2026-10-28T20:00:00+08:00")
    first = graph.invoke(_state("run-dup-1", request), config={"configurable": {"thread_id": "run-dup-1"}})
    second = graph.invoke(_state("run-dup-2", request), config={"configurable": {"thread_id": "run-dup-2"}})

    assert first["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert second["draft_save_status"] == DraftSaveStatus.DUPLICATE_REUSED.value
    assert second["final_response"]["review_status"] == ReviewStatus.APPROVED.value
    assert second["draft_id"] == first["draft_id"]
    assert repository.count_drafts() == 1


def test_invalid_agent_action_uses_legal_fallback(repository, sqlite_checkpointer) -> None:
    class InvalidDecisionEngine:
        def choose(self, legal_actions, state):
            return "PUBLISH"

    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=InvalidDecisionEngine())
    request = _request("M02", "2026-10-28T20:00:00+08:00")
    result = graph.invoke(_state("run-invalid-action", request), config={"configurable": {"thread_id": "run-invalid-action"}})

    assert result["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert result["validated_action"] == "SAVE_DRAFT"
    assert repository.count_drafts() == 1


def test_material_not_found_returns_error_without_saving_draft(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    request = _request("M99", "2026-10-28T20:00:00+08:00")

    result = graph.invoke(_state("run-not-found", request), config={"configurable": {"thread_id": "run-not-found"}})

    assert result["final_response"]["error_code"] == "MATERIAL_NOT_FOUND"
    assert result["draft_save_status"] == DraftSaveStatus.NOT_ATTEMPTED.value
    assert repository.count_drafts() == 0


def test_confirmation_resumes_after_graph_is_reconstructed(repository, database_path, deterministic_decision_engine) -> None:
    request = _request("M01", M01_REQUESTED_TIME)
    config = {"configurable": {"thread_id": "run-restart"}}

    first_checkpointer, first_connection = create_sqlite_checkpointer(database_path)
    try:
        first_graph = build_workflow(repository, first_checkpointer, decision_engine=deterministic_decision_engine)
        interrupted = first_graph.invoke(_state("run-restart", request), config=config)
        assert "__interrupt__" in interrupted
    finally:
        first_connection.close()

    second_checkpointer, second_connection = create_sqlite_checkpointer(database_path)
    try:
        second_graph = build_workflow(repository, second_checkpointer, decision_engine=deterministic_decision_engine)
        resumed = second_graph.invoke(
            Command(resume={"confirmed": True, "selected_time": M01_ALTERNATIVE_TIME}),
            config=config,
        )
    finally:
        second_connection.close()

    assert resumed["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert repository.count_drafts() == 1


def test_alternative_rechecks_availability_and_requests_confirmation_again(repository, sqlite_checkpointer, deterministic_decision_engine) -> None:
    graph = build_workflow(repository, sqlite_checkpointer, decision_engine=deterministic_decision_engine)
    config = {"configurable": {"thread_id": "run-expired-alternative"}}
    request = _request("M01", M01_REQUESTED_TIME)
    interrupted = graph.invoke(_state("run-expired-alternative", request), config=config)
    assert "__interrupt__" in interrupted

    occupied = repository.create_or_get_draft(
        material_id="M02",
        scheduled_time=M01_ALTERNATIVE_TIME,
        schedule_scope="main",
        idempotency_key="other-material-occupies-19",
    )
    assert occupied.status is DraftSaveStatus.SAVED

    renewed = graph.invoke(
        Command(resume={"confirmed": True, "selected_time": M01_ALTERNATIVE_TIME}),
        config=config,
    )

    assert "__interrupt__" in renewed
    assert renewed["__interrupt__"][0].value["alternatives"] == ["2026-10-28T20:00:00+08:00"]
    assert repository.count_drafts() == 1

    saved = graph.invoke(
        Command(resume={"confirmed": True, "selected_time": "2026-10-28T20:00:00+08:00"}),
        config=config,
    )

    assert saved["draft_save_status"] == DraftSaveStatus.SAVED.value
    assert saved["selected_time"] == "2026-10-28T20:00:00+08:00"
    assert repository.count_drafts() == 2
