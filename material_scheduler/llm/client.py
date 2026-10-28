from __future__ import annotations

import sys
import json
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from ..config import Settings
from .decision_tools import DecisionAction, choose_safe_action
from .prompts import DECISION_SYSTEM_PROMPT


class DecisionOutput(BaseModel):
    action: DecisionAction
    reason: str


@dataclass(frozen=True)
class DecisionResult:
    action: DecisionAction
    source: str
    reason: str | None = None


class DecisionEngine:
    """A constrained action chooser; guards remain the authorization boundary."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_environment()
        self._missing_config_notice_printed = False

    def decide(self, legal_actions: list[DecisionAction], state: dict) -> DecisionResult:
        if not legal_actions:
            return DecisionResult(DecisionAction.RETURN_RESULT, source="deterministic")
        if not self.settings.llm_configured:
            if not self._missing_config_notice_printed:
                print("LLM configuration is missing; using deterministic fallback.", file=sys.stderr)
                self._missing_config_notice_printed = True
            return DecisionResult(choose_safe_action(legal_actions, None), source="fallback_missing_config")

        try:
            model = ChatOpenAI(
                base_url=self.settings.llm_base_url,
                api_key=self.settings.llm_api_key,
                model=self.settings.llm_model,
                temperature=0,
            )
            response = model.invoke(
                [
                    (
                        "system",
                        f"{DECISION_SYSTEM_PROMPT}\n"
                        "Return exactly one JSON object with string fields `action` and `reason`. "
                        "Do not use markdown fences or tool calls.",
                    ),
                    (
                        "user",
                        json.dumps(
                            {
                                "legal_actions": [action.value for action in legal_actions],
                                "state": self._safe_state(state),
                            },
                            ensure_ascii=False,
                        ),
                    ),
                ]
            )
            content = response.content
            if not isinstance(content, str):
                raise TypeError("LLM response content is not text")
            payload = json.loads(self._extract_json_object(content))
            response = DecisionOutput.model_validate(payload)
            return DecisionResult(
                choose_safe_action(legal_actions, response.action),
                source="live_llm",
                reason=response.reason,
            )
        except Exception as error:
            # Network/model failures are conservative: only a legal fallback is returned.
            print(f"LLM request failed ({type(error).__name__}); using deterministic fallback.", file=sys.stderr)
            return DecisionResult(choose_safe_action(legal_actions, None), source="fallback_request_error")

    def choose(self, legal_actions: list[DecisionAction], state: dict) -> DecisionAction:
        """Compatibility helper for graph callers that only need the action."""
        return self.decide(legal_actions, state).action

    @staticmethod
    def _safe_state(state: dict) -> dict:
        keys = (
            "material_id",
            "requested_time",
            "review_status",
            "requested_slot_available",
            "offered_alternatives",
            "confirmation_status",
            "draft_save_status",
        )
        return {key: state.get(key) for key in keys}

    @staticmethod
    def _extract_json_object(content: str) -> str:
        """Accept a JSON object optionally wrapped in a markdown fence."""
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[1] if "\n" in stripped else ""
            if stripped.endswith("```"):
                stripped = stripped[:-3].strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end < start:
            raise ValueError("LLM response did not contain a JSON object")
        return stripped[start : end + 1]
