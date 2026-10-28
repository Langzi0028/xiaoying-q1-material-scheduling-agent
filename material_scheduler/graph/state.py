from typing import NotRequired, TypedDict


class SchedulingState(TypedDict):
    run_id: str
    request_id: str
    material_id: str
    requested_time: str
    time_requirement_type: str
    schedule_scope: str
    idempotency_key: str
    max_steps: NotRequired[int]
    execution_steps: NotRequired[int]
    execution_limit_reached: NotRequired[bool]
    material: NotRequired[dict | None]
    review_status: NotRequired[str | None]
    risk_reasons: NotRequired[list[str]]
    missing_fields: NotRequired[list[str]]
    requested_slot_available: NotRequired[bool | None]
    conflicts: NotRequired[list[str]]
    offered_alternatives: NotRequired[list[str]]
    suggested_time: NotRequired[str | None]
    selected_time: NotRequired[str | None]
    confirmation_status: NotRequired[str]
    needs_confirmation: NotRequired[bool]
    legal_actions: NotRequired[list[str]]
    proposed_action: NotRequired[str | None]
    decision_source: NotRequired[str | None]
    decision_reason: NotRequired[str | None]
    validated_action: NotRequired[str | None]
    draft_save_status: NotRequired[str]
    draft_id: NotRequired[str | None]
    error_code: NotRequired[str | None]
    error_message: NotRequired[str | None]
    final_response: NotRequired[dict | None]
