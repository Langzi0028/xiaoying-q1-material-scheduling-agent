from __future__ import annotations

import pytest

from material_scheduler.config import Settings
from material_scheduler.llm.client import DecisionEngine
from material_scheduler.llm.decision_tools import DecisionAction


def test_settings_loads_root_dotenv_without_overwriting_shell_values(tmp_path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "LLM_BASE_URL=https://dotenv.example/v1\nLLM_API_KEY=dotenv-key\nLLM_MODEL=dotenv-model\n",
        encoding="utf-8",
    )
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LLM_MODEL", "shell-model")

    settings = Settings.from_environment(project_root=tmp_path)

    assert settings.llm_base_url == "https://dotenv.example/v1"
    assert settings.llm_api_key == "dotenv-key"
    assert settings.llm_model == "shell-model"


def test_missing_llm_notice_goes_to_stderr_and_falls_back(capsys) -> None:
    engine = DecisionEngine(Settings(database_path="data/test.db", llm_base_url=None, llm_api_key=None, llm_model=None))

    action = engine.choose([DecisionAction.SAVE_DRAFT], {})

    captured = capsys.readouterr()
    assert action is DecisionAction.SAVE_DRAFT
    assert "LLM configuration is missing" in captured.err
    assert captured.out == ""

    engine.choose([DecisionAction.RETURN_RESULT], {})
    assert capsys.readouterr().err == ""

    result = engine.decide([DecisionAction.RETURN_RESULT], {})
    assert result.source == "fallback_missing_config"


def test_llm_failure_notice_exposes_only_exception_type(monkeypatch, capsys) -> None:
    settings = Settings(
        database_path="data/test.db",
        llm_base_url="https://private-gateway.example/v1",
        llm_api_key="secret-key",
        llm_model="test-model",
    )

    class FailingModel:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            raise RuntimeError("https://private-gateway.example/v1 leaked details")

    import material_scheduler.llm.client as llm_client

    monkeypatch.setattr(llm_client, "ChatOpenAI", lambda **kwargs: FailingModel())
    action = DecisionEngine(settings).choose([DecisionAction.RETURN_RESULT], {})

    captured = capsys.readouterr()
    assert action is DecisionAction.RETURN_RESULT
    assert "RuntimeError" in captured.err
    assert "private-gateway" not in captured.err
    assert "secret-key" not in captured.err
    assert captured.out == ""

    result = DecisionEngine(settings).decide([DecisionAction.RETURN_RESULT], {})
    assert result.source == "fallback_request_error"


def test_openai_compatible_json_response_is_parsed_as_live_llm(monkeypatch) -> None:
    settings = Settings(
        database_path="data/test.db",
        llm_base_url="https://example.invalid/v1",
        llm_api_key="test-key",
        llm_model="test-model",
    )

    class Response:
        content = '{"action":"REQUEST_CONFIRMATION","reason":"The requested slot conflicts."}'

    class JsonModel:
        def invoke(self, messages):
            return Response()

    monkeypatch.setattr("material_scheduler.llm.client.ChatOpenAI", lambda **kwargs: JsonModel())
    result = DecisionEngine(settings).decide(
        [DecisionAction.REQUEST_CONFIRMATION, DecisionAction.RETURN_RESULT],
        {"requested_slot_available": False},
    )

    assert result.source == "live_llm"
    assert result.action is DecisionAction.REQUEST_CONFIRMATION
    assert result.reason == "The requested slot conflicts."
