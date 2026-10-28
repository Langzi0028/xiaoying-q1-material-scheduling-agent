from __future__ import annotations

from ..enums import ConfirmationStatus, ReviewStatus


class GuardError(ValueError):
    pass


class ConfirmationRequiredError(GuardError):
    pass


class ReviewNotApprovedError(GuardError):
    pass


class InvalidAlternativeError(GuardError):
    pass


def validate_before_save(state: dict) -> None:
    if state.get("review_status") != ReviewStatus.APPROVED.value:
        raise ReviewNotApprovedError("Only approved material can be saved as a draft")

    requested_time = state.get("requested_time")
    selected_time = state.get("selected_time") or requested_time
    if not selected_time:
        raise GuardError("A selected time is required before saving")

    is_alternative = selected_time != requested_time
    if is_alternative:
        if selected_time not in state.get("offered_alternatives", []):
            raise InvalidAlternativeError("Selected time was not offered as an available alternative")
        if state.get("confirmation_status") != ConfirmationStatus.CONFIRMED.value:
            raise ConfirmationRequiredError("A replacement slot requires explicit confirmation")

    if state.get("requested_slot_available") is False and not is_alternative:
        raise ConfirmationRequiredError("Conflicted requested slot cannot be saved")
