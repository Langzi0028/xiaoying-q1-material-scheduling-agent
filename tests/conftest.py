import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from material_scheduler.fixtures.scenarios import seed_demo_data
from material_scheduler.llm.decision_tools import DecisionAction
from material_scheduler.storage.database import Database
from material_scheduler.storage.repositories import Repository
from langgraph.checkpoint.sqlite import SqliteSaver


@pytest.fixture()
def database_path() -> Path:
    root = Path.cwd() / "data" / ".test-runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{uuid4().hex}.db"


@pytest.fixture()
def repository(database_path: Path) -> Repository:
    database = Database(database_path)
    database.initialize()
    repository = Repository(database)
    seed_demo_data(repository)
    return repository


@pytest.fixture()
def sqlite_checkpointer(database_path: Path):
    connection = sqlite3.connect(database_path, check_same_thread=False)
    saver = SqliteSaver(connection)
    try:
        yield saver
    finally:
        connection.close()


@pytest.fixture()
def deterministic_decision_engine():
    class DeterministicDecisionEngine:
        def decide(self, legal_actions, state):
            from material_scheduler.llm.client import DecisionResult

            return DecisionResult(legal_actions[0], source="test_deterministic")

        def choose(self, legal_actions, state):
            return legal_actions[0]

    return DeterministicDecisionEngine()
