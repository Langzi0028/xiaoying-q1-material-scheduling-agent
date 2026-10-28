from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..llm.client import DecisionEngine
from ..storage.repositories import Repository
from ..trace import TraceRecorder
from .nodes import NodeFactory
from .routing import after_alternatives, after_confirmation, after_existing_draft, after_guard, after_slot_check, after_validated_action
from .state import SchedulingState


def _with_execution_limit(node, *, count_step: bool = True):
    def limited_node(state: dict):
        steps = state.get("execution_steps", 0)
        max_steps = state.get("max_steps", 24)
        if steps >= max_steps:
            return {"execution_steps": steps, "execution_limit_reached": True}

        update = node(state)
        if count_step:
            update.setdefault("execution_steps", steps + 1)
        return update

    return limited_node


def build_workflow(
    repository: Repository,
    checkpointer,
    *,
    decision_engine: DecisionEngine | None = None,
    fail_save: bool = False,
    trace_recorder: TraceRecorder | None = None,
):
    nodes = NodeFactory(
        repository,
        decision_engine or DecisionEngine(),
        fail_save=fail_save,
        trace_recorder=trace_recorder,
    )
    workflow = StateGraph(SchedulingState)
    workflow.add_node("find_existing_draft", _with_execution_limit(nodes.find_existing_draft))
    workflow.add_node("load_material", _with_execution_limit(nodes.load_material))
    workflow.add_node("review_material", _with_execution_limit(nodes.review_material))
    workflow.add_node("check_requested_slot", _with_execution_limit(nodes.check_requested_slot))
    workflow.add_node("find_alternatives", _with_execution_limit(nodes.find_alternatives))
    workflow.add_node("derive_legal_actions", _with_execution_limit(nodes.derive_legal_actions, count_step=False))
    workflow.add_node("decide_next_action", _with_execution_limit(nodes.decide_next_action))
    workflow.add_node("validate_action", _with_execution_limit(nodes.validate_action, count_step=False))
    workflow.add_node("request_confirmation", _with_execution_limit(nodes.request_confirmation))
    workflow.add_node("validate_before_save", _with_execution_limit(nodes.validate_before_save))
    workflow.add_node("save_draft", _with_execution_limit(nodes.save_draft))
    workflow.add_node("finalize", nodes.finalize)

    workflow.add_edge(START, "find_existing_draft")
    workflow.add_conditional_edges("find_existing_draft", after_existing_draft)
    workflow.add_edge("load_material", "review_material")
    workflow.add_edge("review_material", "derive_legal_actions")
    workflow.add_edge("derive_legal_actions", "decide_next_action")
    workflow.add_edge("decide_next_action", "validate_action")
    workflow.add_conditional_edges("validate_action", after_validated_action)
    workflow.add_conditional_edges("check_requested_slot", after_slot_check)
    workflow.add_conditional_edges("find_alternatives", after_alternatives)
    workflow.add_conditional_edges("request_confirmation", after_confirmation)
    workflow.add_conditional_edges("validate_before_save", after_guard)
    workflow.add_edge("save_draft", "finalize")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=checkpointer)
