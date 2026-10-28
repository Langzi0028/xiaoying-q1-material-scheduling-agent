from material_scheduler.llm.decision_tools import DecisionAction, choose_safe_action, validate_action


def test_decision_actions_do_not_expose_publish() -> None:
    assert "PUBLISH" not in {action.value for action in DecisionAction}
    assert DecisionAction.SAVE_DRAFT.value == "SAVE_DRAFT"


def test_invalid_model_action_falls_back_to_first_legal_action() -> None:
    assert choose_safe_action([DecisionAction.REQUEST_CONFIRMATION], "PUBLISH") is DecisionAction.REQUEST_CONFIRMATION


def test_validate_action_rejects_outside_legal_set() -> None:
    assert validate_action(DecisionAction.SAVE_DRAFT, [DecisionAction.REQUEST_CONFIRMATION]) is False
