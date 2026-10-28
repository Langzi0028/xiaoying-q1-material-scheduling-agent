from __future__ import annotations

from langgraph.types import interrupt

from ..enums import ConfirmationStatus, DraftSaveStatus, ErrorCode, ReviewStatus
from ..llm.client import DecisionEngine
from ..llm.decision_tools import DecisionAction, choose_safe_action, validate_action
from ..models import ConfirmationInput, SchedulingResponse
from ..storage.repositories import Repository
from ..tools.drafts import DraftTool
from ..tools.materials import MaterialTool
from ..tools.rules import RuleTool
from ..tools.slots import SlotTool
from ..trace import TraceRecorder
from .guards import GuardError, validate_before_save


class NodeFactory:
    def __init__(
        self,
        repository: Repository,
        decision_engine: DecisionEngine,
        *,
        fail_save: bool = False,
        trace_recorder: TraceRecorder | None = None,
    ) -> None:
        self.repository = repository
        self.materials = MaterialTool(repository)
        self.rules = RuleTool()
        self.slots = SlotTool(repository)
        self.drafts = DraftTool(repository, fail_save=fail_save)
        self.decision_engine = decision_engine
        self.trace_recorder = trace_recorder

    def _trace(self, node: str, update: dict) -> dict:
        if self.trace_recorder is not None:
            self.trace_recorder.record(node, update)
        return update

    def find_existing_draft(self, state: dict) -> dict:
        draft = self.repository.find_draft_by_idempotency_key(state["idempotency_key"])
        if draft is None:
            return self._trace("find_existing_draft", {})
        return self._trace("find_existing_draft", {
            "review_status": ReviewStatus.APPROVED.value,
            "draft_save_status": DraftSaveStatus.DUPLICATE_REUSED.value,
            "draft_id": draft.draft_id,
            "selected_time": draft.scheduled_time,
            "suggested_time": draft.scheduled_time,
            "confirmation_status": ConfirmationStatus.CONFIRMED.value,
        })

    def load_material(self, state: dict) -> dict:
        material = self.materials.get_material(state["material_id"])
        if material is None:
            return self._trace("load_material", {
                "material": None,
                "error_code": ErrorCode.MATERIAL_NOT_FOUND.value,
                "error_message": f"未找到素材 {state['material_id']}",
            })
        return self._trace("load_material", {"material": material.model_dump()})

    def review_material(self, state: dict) -> dict:
        if state.get("material") is None:
            return self._trace("review_material", {})
        from ..models import Material

        result = self.rules.check_rules(Material.model_validate(state["material"]))
        update = {
            "review_status": result.status.value,
            "risk_reasons": result.risk_reasons,
            "missing_fields": result.missing_fields,
        }
        if result.status is ReviewStatus.NEEDS_INFO:
            update.update(
                error_code=ErrorCode.MISSING_METADATA.value,
                error_message="素材信息不完整，需要补充后再排期",
            )
        elif result.status is ReviewStatus.BLOCKED:
            update.update(
                error_code=ErrorCode.RULE_BLOCKED.value,
                error_message="素材命中审核阻断规则",
            )
        return self._trace("review_material", update)

    def check_requested_slot(self, state: dict) -> dict:
        result = self.slots.check_slot(
            schedule_scope=state["schedule_scope"],
            requested_time=state["requested_time"],
        )
        update = {
            "requested_slot_available": result.available,
            "conflicts": result.conflicts,
        }
        if result.available:
            update["selected_time"] = result.requested_time
            update["suggested_time"] = result.requested_time
        return self._trace("check_requested_slot", update)

    def find_alternatives(self, state: dict) -> dict:
        alternatives = self.slots.find_alternatives(
            schedule_scope=state["schedule_scope"],
            requested_time=state["requested_time"],
        )
        if not alternatives:
            return self._trace("find_alternatives", {
                "offered_alternatives": [],
                "error_code": ErrorCode.NO_SLOT_AVAILABLE.value,
                "error_message": "没有可用的替代时段，请用户重新指定时间范围",
            })
        return self._trace("find_alternatives", {
            "offered_alternatives": alternatives,
            "suggested_time": alternatives[0],
            "needs_confirmation": True,
        })

    def derive_legal_actions(self, state: dict) -> dict:
        legal: list[DecisionAction]
        if state.get("error_code") or state.get("review_status") in {
            ReviewStatus.NEEDS_INFO.value,
            ReviewStatus.BLOCKED.value,
        }:
            legal = [DecisionAction.RETURN_RESULT]
        elif state.get("review_status") != ReviewStatus.APPROVED.value:
            legal = [DecisionAction.RETURN_RESULT]
        elif state.get("requested_slot_available") is None:
            legal = [DecisionAction.CHECK_REQUESTED_SLOT]
        elif state.get("requested_slot_available") is False and not state.get("offered_alternatives"):
            legal = [DecisionAction.CHECK_ALTERNATIVES]
        elif state.get("needs_confirmation") and state.get("confirmation_status") != ConfirmationStatus.CONFIRMED.value:
            legal = [DecisionAction.REQUEST_CONFIRMATION]
        elif state.get("confirmation_status") == ConfirmationStatus.REJECTED.value:
            legal = [DecisionAction.RETURN_RESULT]
        elif state.get("draft_save_status") in {
            DraftSaveStatus.SAVED.value,
            DraftSaveStatus.DUPLICATE_REUSED.value,
            DraftSaveStatus.FAILED.value,
        }:
            legal = [DecisionAction.RETURN_RESULT]
        else:
            legal = [DecisionAction.SAVE_DRAFT]
        return self._trace("derive_legal_actions", {"legal_actions": [action.value for action in legal]})

    def decide_next_action(self, state: dict) -> dict:
        legal = [DecisionAction(value) for value in state.get("legal_actions", [])]
        if hasattr(self.decision_engine, "decide"):
            decision = self.decision_engine.decide(legal, state)
            update = {
                "proposed_action": decision.action.value,
                "decision_source": decision.source,
                "decision_reason": decision.reason,
            }
        else:
            action = self.decision_engine.choose(legal, state)
            update = {
                "proposed_action": action.value if isinstance(action, DecisionAction) else str(action),
                "decision_source": "injected_test_engine",
            }
        return self._trace("decide_next_action", update)

    def validate_action(self, state: dict) -> dict:
        legal = [DecisionAction(value) for value in state.get("legal_actions", [])]
        proposed = state.get("proposed_action")
        if validate_action(proposed, legal):
            return self._trace("validate_action", {"validated_action": proposed})
        fallback = choose_safe_action(legal, None)
        return self._trace("validate_action", {
            "validated_action": fallback.value,
        })

    def request_confirmation(self, state: dict) -> dict:
        payload = {
            "message": "目标时段冲突，请确认替代时段；尚未保存草稿，尚未发布。",
            "requested_time": state["requested_time"],
            "conflicts": state.get("conflicts", []),
            "alternatives": state.get("offered_alternatives", []),
        }
        self._trace("request_confirmation", {"status": "interrupt_requested", "payload": payload})
        answer = interrupt(payload)
        confirmation = ConfirmationInput.model_validate(answer)
        if not confirmation.confirmed:
            return self._trace("request_confirmation", {
                "confirmation_status": ConfirmationStatus.REJECTED.value,
                "needs_confirmation": False,
                "error_message": "用户拒绝替代时段，未保存草稿",
            })
        if confirmation.selected_time not in state.get("offered_alternatives", []):
            return self._trace("request_confirmation", {
                "confirmation_status": ConfirmationStatus.PENDING.value,
                "error_code": ErrorCode.INVALID_CONFIRMATION.value,
                "error_message": "确认的时段不在已提供的替代时段中",
            })
        slot = self.slots.check_slot(
            schedule_scope=state["schedule_scope"],
            requested_time=confirmation.selected_time,
        )
        if not slot.available:
            return self._trace("request_confirmation", {
                "confirmation_status": ConfirmationStatus.PENDING.value,
                "selected_time": None,
                "offered_alternatives": slot.alternatives,
                "suggested_time": slot.alternatives[0] if slot.alternatives else None,
                "error_code": None,
                "error_message": None,
            })
        return self._trace("request_confirmation", {
            "confirmation_status": ConfirmationStatus.CONFIRMED.value,
            "needs_confirmation": False,
            "selected_time": confirmation.selected_time,
        })

    def validate_before_save(self, state: dict) -> dict:
        try:
            validate_before_save(state)
        except GuardError as error:
            return self._trace("validate_before_save", {"error_code": ErrorCode.CONFIRMATION_REQUIRED.value, "error_message": str(error)})
        return self._trace("validate_before_save", {})

    def save_draft(self, state: dict) -> dict:
        result = self.drafts.save_draft(
            material_id=state["material_id"],
            selected_time=state.get("selected_time") or state["requested_time"],
            schedule_scope=state["schedule_scope"],
            idempotency_key=state["idempotency_key"],
        )
        return self._trace("save_draft", {
            "draft_save_status": result.status.value,
            "draft_id": result.draft.draft_id if result.draft else None,
            "selected_time": result.draft.scheduled_time if result.draft else state.get("selected_time"),
            "error_code": result.error_code.value if result.error_code else None,
            "error_message": result.error_message,
        })

    def finalize(self, state: dict) -> dict:
        execution_limited = state.get("execution_limit_reached", False)
        response = SchedulingResponse(
            run_id=state["run_id"],
            material_id=state["material_id"],
            review_status=state.get("review_status"),
            risk_reasons=state.get("risk_reasons", []),
            missing_fields=state.get("missing_fields", []),
            requested_time=state["requested_time"],
            suggested_time=state.get("suggested_time"),
            confirmation_status=state.get("confirmation_status", ConfirmationStatus.NOT_REQUIRED.value),
            pending_confirmation=self._pending_confirmation(state),
            draft_save_status=state.get("draft_save_status", DraftSaveStatus.NOT_ATTEMPTED.value),
            draft_id=state.get("draft_id"),
            error_code=ErrorCode.EXECUTION_LIMIT_REACHED if execution_limited else state.get("error_code"),
            execution_status="incomplete" if execution_limited else "completed",
            message=self._message(state),
        )
        return self._trace("finalize", {
            "draft_save_status": response.draft_save_status.value,
            "confirmation_status": response.confirmation_status.value,
            "final_response": response.model_dump(mode="json"),
        })

    @staticmethod
    def _pending_confirmation(state: dict) -> list[str]:
        if state.get("confirmation_status") == ConfirmationStatus.PENDING.value or state.get("offered_alternatives") and state.get("selected_time") is None:
            suggestion = state.get("suggested_time")
            return [*state.get("conflicts", []), f"是否确认使用 {suggestion}？"]
        return []

    @staticmethod
    def _message(state: dict) -> str:
        if state.get("execution_limit_reached"):
            return "已达到执行步骤上限，未形成草稿，尚未发布。"
        if state.get("draft_save_status") == DraftSaveStatus.SAVED.value:
            return "排期草稿已保存，尚未发布。"
        if state.get("draft_save_status") == DraftSaveStatus.DUPLICATE_REUSED.value:
            return "已复用已有排期草稿，尚未发布。"
        if state.get("draft_save_status") == DraftSaveStatus.FAILED.value:
            return f"草稿保存失败：{state.get('error_message') or '未知错误'}；未创建草稿，尚未发布。"
        if state.get("review_status") == ReviewStatus.NEEDS_INFO.value:
            return "素材信息缺失，等待补充；尚未保存草稿，更未发布。"
        if state.get("review_status") == ReviewStatus.BLOCKED.value:
            return "素材审核被阻断；尚未保存草稿，更未发布。"
        if state.get("confirmation_status") == ConfirmationStatus.REJECTED.value:
            return "用户未确认替代时段，未保存草稿，更未发布。"
        if state.get("offered_alternatives"):
            return "已完成审核，等待用户确认替代时段；尚未保存草稿，更未发布。"
        return state.get("error_message") or "未形成草稿，更未发布。"
