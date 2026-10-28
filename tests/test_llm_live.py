import pytest

from material_scheduler.config import Settings
from material_scheduler.llm.client import DecisionEngine
from material_scheduler.llm.decision_tools import DecisionAction


def test_real_llm_makes_a_constrained_decision() -> None:
    settings = Settings.from_environment()
    if not settings.llm_configured:
        pytest.skip("真实 LLM 凭据未配置；跳过在线模型验证，不把离线决策测试当作真实 LLM 验证。")

    result = DecisionEngine(settings).decide(
        [DecisionAction.REQUEST_CONFIRMATION, DecisionAction.RETURN_RESULT],
        {
            "material_id": "M01",
            "requested_time": "2026-10-28T18:00:00+08:00",
            "requested_slot_available": False,
            "offered_alternatives": ["2026-10-28T19:00:00+08:00"],
            "confirmation_status": "pending",
        },
    )

    assert settings.llm_configured is True
    assert result.source == "live_llm"
    assert result.action in {DecisionAction.REQUEST_CONFIRMATION, DecisionAction.RETURN_RESULT}
    assert result.reason
