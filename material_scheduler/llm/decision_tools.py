from enum import StrEnum


class DecisionAction(StrEnum):
    REQUEST_MISSING_INFO = "REQUEST_MISSING_INFO"
    BLOCK_SCHEDULING = "BLOCK_SCHEDULING"
    CHECK_REQUESTED_SLOT = "CHECK_REQUESTED_SLOT"
    CHECK_ALTERNATIVES = "CHECK_ALTERNATIVES"
    REQUEST_CONFIRMATION = "REQUEST_CONFIRMATION"
    SAVE_DRAFT = "SAVE_DRAFT"
    RETURN_RESULT = "RETURN_RESULT"


def validate_action(action: DecisionAction | str, legal_actions: list[DecisionAction]) -> bool:
    try:
        normalized = DecisionAction(action)
    except ValueError:
        return False
    return normalized in legal_actions


def choose_safe_action(legal_actions: list[DecisionAction], proposed_action: DecisionAction | str | None) -> DecisionAction:
    """Use a model proposal only when it passes the deterministic allow-list."""
    if not legal_actions:
        return DecisionAction.RETURN_RESULT
    try:
        candidate = DecisionAction(proposed_action) if proposed_action is not None else None
    except ValueError:
        candidate = None
    return candidate if candidate in legal_actions else legal_actions[0]
