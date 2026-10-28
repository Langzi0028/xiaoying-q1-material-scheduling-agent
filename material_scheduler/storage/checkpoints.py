from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def create_sqlite_checkpointer(path: Path | str) -> tuple[SqliteSaver, sqlite3.Connection]:
    connection = sqlite3.connect(path, check_same_thread=False)
    return SqliteSaver(connection), connection
