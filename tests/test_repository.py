from material_scheduler.enums import DraftSaveStatus


def test_repository_reuses_draft_for_same_request_fingerprint(repository) -> None:
    first = repository.create_or_get_draft(
        material_id="M02",
        scheduled_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="same-key",
    )
    second = repository.create_or_get_draft(
        material_id="M02",
        scheduled_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="same-key",
    )

    assert first.status is DraftSaveStatus.SAVED
    assert second.status is DraftSaveStatus.DUPLICATE_REUSED
    assert second.draft is not None
    assert second.draft.draft_id == first.draft.draft_id
    assert repository.count_drafts() == 1


def test_repository_rejects_different_material_in_same_scope_and_slot(repository) -> None:
    repository.create_or_get_draft(
        material_id="M02",
        scheduled_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="first-key",
    )

    result = repository.create_or_get_draft(
        material_id="M01",
        scheduled_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="second-key",
    )

    assert result.status is DraftSaveStatus.FAILED
    assert result.error_code.value == "SLOT_CONFLICT"
    assert repository.count_drafts() == 1


def test_repository_reuses_equivalent_timestamp_offsets(repository) -> None:
    first = repository.create_or_get_draft(
        material_id="M02",
        scheduled_time="2026-10-28T12:00:00Z",
        schedule_scope="main",
        idempotency_key="offset-key",
    )
    second = repository.create_or_get_draft(
        material_id="M02",
        scheduled_time="2026-10-28T20:00:00+08:00",
        schedule_scope="main",
        idempotency_key="offset-key",
    )

    assert first.status is DraftSaveStatus.SAVED
    assert second.status is DraftSaveStatus.DUPLICATE_REUSED
    assert repository.count_drafts() == 1
