from material_scheduler.enums import DraftSaveStatus, ReviewStatus
from material_scheduler.tools.drafts import DraftTool
from material_scheduler.tools.materials import MaterialTool
from material_scheduler.tools.rules import RuleTool
from material_scheduler.tools.slots import SlotTool


def test_missing_metadata_returns_needs_info(repository) -> None:
    material = MaterialTool(repository).get_material("M03")
    review = RuleTool().check_rules(material)

    assert review.status is ReviewStatus.NEEDS_INFO
    assert review.missing_fields == ["copyright_status"]


def test_risky_material_is_blocked(repository) -> None:
    material = MaterialTool(repository).get_material("M04")
    review = RuleTool().check_rules(material)

    assert review.status is ReviewStatus.BLOCKED
    assert review.risk_reasons == ["sensitive_content"]


def test_slot_lookup_reports_occupied_requested_slot_and_available_alternative(repository) -> None:
    result = SlotTool(repository).check_slot(
        schedule_scope="main",
        requested_time="2026-10-28T18:00:00+08:00",
    )

    assert result.available is False
    assert result.alternatives == ["2026-10-28T19:00:00+08:00"]


def test_slot_lookup_treats_saved_draft_as_occupied(repository) -> None:
    draft_tool = DraftTool(repository)
    draft_tool.save_draft(
        material_id="M02",
        selected_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="draft-slot-key",
    )

    result = SlotTool(repository).check_slot(
        schedule_scope="main",
        requested_time="2026-10-28T20:00:00+08:00",
    )

    assert result.available is False
    assert "草稿素材 M02" in result.conflicts[0]


def test_injected_draft_save_failure_is_honest_and_creates_no_row(repository) -> None:
    result = DraftTool(repository, fail_save=True).save_draft(
        material_id="M02",
        selected_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="failing-save-key",
    )

    assert result.status is DraftSaveStatus.FAILED
    assert result.error_message == "模拟数据库写入异常"
    assert repository.count_drafts() == 0
