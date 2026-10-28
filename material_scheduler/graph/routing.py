from __future__ import annotations

from ..llm.decision_tools import DecisionAction


def _limit_reached(state: dict) -> bool:
    return bool(state.get("execution_limit_reached"))


def after_existing_draft(state: dict) -> str:
    if _limit_reached(state):
        return "finalize"
    return "finalize" if state.get("draft_save_status") == "duplicate_reused" else "load_material"


def after_validated_action(state: dict) -> str:
    if _limit_reached(state):
        return "finalize"
    action = state.get("validated_action")
    routes = {
        DecisionAction.CHECK_REQUESTED_SLOT.value: "check_requested_slot",
        DecisionAction.CHECK_ALTERNATIVES.value: "find_alternatives",
        DecisionAction.REQUEST_CONFIRMATION.value: "request_confirmation",
        DecisionAction.SAVE_DRAFT.value: "validate_before_save",
        DecisionAction.REQUEST_MISSING_INFO.value: "finalize",
        DecisionAction.BLOCK_SCHEDULING.value: "finalize",
        DecisionAction.RETURN_RESULT.value: "finalize",
    }
    return routes.get(action, "finalize")


def after_slot_check(state: dict) -> str:
    if _limit_reached(state):
        return "finalize"
    return "derive_legal_actions"


def after_alternatives(state: dict) -> str:
    if _limit_reached(state):
        return "finalize"
    return "derive_legal_actions"


def after_confirmation(state: dict) -> str:
    if _limit_reached(state):
        return "finalize"
    if state.get("confirmation_status") == "rejected":
        return "finalize"
    if state.get("confirmation_status") == "pending":
        return "request_confirmation"
    return "derive_legal_actions"


def after_guard(state: dict) -> str:
    if _limit_reached(state):
        return "finalize"
    return "save_draft" if not state.get("error_code") else "finalize"
