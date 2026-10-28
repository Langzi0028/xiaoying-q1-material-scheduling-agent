import pytest

from material_scheduler.enums import ConfirmationStatus, ReviewStatus, TimeRequirementType
from material_scheduler.graph.guards import ConfirmationRequiredError, validate_before_save


def test_unconfirmed_alternative_cannot_be_saved() -> None:
    state = {
        "review_status": ReviewStatus.APPROVED.value,
        "requested_slot_available": False,
        "offered_alternatives": ["2026-10-28T19:00:00+08:00"],
        "selected_time": "2026-10-28T19:00:00+08:00",
        "confirmation_status": ConfirmationStatus.PENDING.value,
        "requested_time": "2026-10-28T18:00:00+08:00",
        "time_requirement_type": TimeRequirementType.PREFERRED.value,
    }

    with pytest.raises(ConfirmationRequiredError):
        validate_before_save(state)


def test_hard_time_change_can_be_saved_after_explicit_confirmation() -> None:
    state = {
        "review_status": ReviewStatus.APPROVED.value,
        "requested_slot_available": False,
        "offered_alternatives": ["2026-10-28T19:00:00+08:00"],
        "selected_time": "2026-10-28T19:00:00+08:00",
        "confirmation_status": ConfirmationStatus.CONFIRMED.value,
        "requested_time": "2026-10-28T18:00:00+08:00",
        "time_requirement_type": TimeRequirementType.HARD.value,
    }

    validate_before_save(state)


def test_confirmed_offered_preferred_alternative_can_be_saved() -> None:
    state = {
        "review_status": ReviewStatus.APPROVED.value,
        "requested_slot_available": False,
        "offered_alternatives": ["2026-10-28T19:00:00+08:00"],
        "selected_time": "2026-10-28T19:00:00+08:00",
        "confirmation_status": ConfirmationStatus.CONFIRMED.value,
        "requested_time": "2026-10-28T18:00:00+08:00",
        "time_requirement_type": TimeRequirementType.PREFERRED.value,
    }

    validate_before_save(state)
