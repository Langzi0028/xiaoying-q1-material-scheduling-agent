from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS materials (
                    material_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    material_type TEXT NOT NULL,
                    copyright_status TEXT,
                    content_risk TEXT,
                    schedule_scope TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scheduling_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL,
                    rule_value TEXT NOT NULL,
                    severity TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS occupied_slots (
                    schedule_scope TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    PRIMARY KEY (schedule_scope, scheduled_time)
                );

                CREATE TABLE IF NOT EXISTS drafts (
                    draft_id TEXT PRIMARY KEY,
                    material_id TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    schedule_scope TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status = 'draft'),
                    idempotency_key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    UNIQUE (schedule_scope, scheduled_time)
                );

                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
