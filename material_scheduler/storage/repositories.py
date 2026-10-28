from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from ..enums import DraftSaveStatus, ErrorCode, RunStatus
from ..models import DraftRecord, DraftSaveResult, Material, RunRecord, SchedulingRequest, SchedulingResponse, canonicalize_time
from .database import Database


class Repository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add_material(self, material: Material) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO materials (
                    material_id, title, material_type, copyright_status, content_risk, schedule_scope
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    material.material_id,
                    material.title,
                    material.material_type,
                    material.copyright_status,
                    material.content_risk,
                    material.schedule_scope,
                ),
            )

    def add_occupied_slot(self, schedule_scope: str, scheduled_time: str, reason: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO occupied_slots (schedule_scope, scheduled_time, reason) VALUES (?, ?, ?)",
                (schedule_scope, canonicalize_time(scheduled_time), reason),
            )

    def get_material(self, material_id: str) -> Material | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM materials WHERE material_id = ?", (material_id,)).fetchone()
        return Material(**dict(row)) if row is not None else None

    def find_draft_by_idempotency_key(self, idempotency_key: str) -> DraftRecord | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM drafts WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
        return self._draft_from_row(row) if row is not None else None

    def get_slot_conflict(self, schedule_scope: str, scheduled_time: str) -> str | None:
        normalized_time = canonicalize_time(scheduled_time)
        with self.database.connect() as connection:
            occupied = connection.execute(
                "SELECT reason FROM occupied_slots WHERE schedule_scope = ? AND scheduled_time = ?",
                (schedule_scope, normalized_time),
            ).fetchone()
            if occupied is not None:
                return occupied["reason"]
            draft = connection.execute(
                "SELECT material_id FROM drafts WHERE schedule_scope = ? AND scheduled_time = ?",
                (schedule_scope, normalized_time),
            ).fetchone()
        return f"草稿素材 {draft['material_id']} 已占用该时段" if draft is not None else None

    def list_drafts(self) -> list[DraftRecord]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM drafts ORDER BY created_at").fetchall()
        return [self._draft_from_row(row) for row in rows]

    def create_or_get_draft(
        self,
        *,
        material_id: str,
        scheduled_time: str,
        schedule_scope: str,
        idempotency_key: str,
        fail_save: bool = False,
    ) -> DraftSaveResult:
        if fail_save:
            return DraftSaveResult(
                status=DraftSaveStatus.FAILED,
                error_code=ErrorCode.SAVE_FAILED,
                error_message="模拟数据库写入异常",
            )

        normalized_time = canonicalize_time(scheduled_time)
        existing = self.find_draft_by_idempotency_key(idempotency_key)
        if existing is not None:
            return DraftSaveResult(status=DraftSaveStatus.DUPLICATE_REUSED, draft=existing)

        draft = DraftRecord(
            draft_id=f"draft_{uuid.uuid4().hex[:12]}",
            material_id=material_id,
            scheduled_time=normalized_time,
            schedule_scope=schedule_scope,
            idempotency_key=idempotency_key,
        )
        try:
            with self.database.connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                conflict = connection.execute(
                    "SELECT reason FROM occupied_slots WHERE schedule_scope = ? AND scheduled_time = ?",
                    (schedule_scope, normalized_time),
                ).fetchone()
                if conflict is not None:
                    connection.rollback()
                    return DraftSaveResult(
                        status=DraftSaveStatus.FAILED,
                        error_code=ErrorCode.SLOT_CONFLICT,
                        error_message=conflict["reason"],
                    )
                connection.execute(
                    """
                    INSERT INTO drafts (
                        draft_id, material_id, scheduled_time, schedule_scope, status, idempotency_key, created_at
                    ) VALUES (?, ?, ?, ?, 'draft', ?, ?)
                    """,
                    (
                        draft.draft_id,
                        draft.material_id,
                        draft.scheduled_time,
                        draft.schedule_scope,
                        draft.idempotency_key,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError:
            existing = self.find_draft_by_idempotency_key(idempotency_key)
            if existing is not None:
                return DraftSaveResult(status=DraftSaveStatus.DUPLICATE_REUSED, draft=existing)
            return DraftSaveResult(
                status=DraftSaveStatus.FAILED,
                error_code=ErrorCode.SLOT_CONFLICT,
                error_message="该排期范围中的时段已被其他草稿占用",
            )
        except sqlite3.DatabaseError as error:
            return DraftSaveResult(
                status=DraftSaveStatus.FAILED,
                error_code=ErrorCode.SAVE_FAILED,
                error_message=str(error),
            )
        return DraftSaveResult(status=DraftSaveStatus.SAVED, draft=draft)

    def count_drafts(self) -> int:
        with self.database.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM drafts").fetchone()[0])

    def create_run(self, run_id: str, request: SchedulingRequest) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO runs (run_id, request_json, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, request.model_dump_json(), RunStatus.RUNNING.value, now, now),
            )

    def update_run(
        self,
        run_id: str,
        status: RunStatus,
        response: SchedulingResponse | dict[str, Any] | None,
    ) -> None:
        response_json = None
        if response is not None:
            response_json = response.model_dump_json() if isinstance(response, SchedulingResponse) else json.dumps(response, ensure_ascii=False)
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE runs SET status = ?, response_json = ?, updated_at = ? WHERE run_id = ?",
                (status.value, response_json, datetime.now(timezone.utc).isoformat(), run_id),
            )

    def get_run(self, run_id: str) -> RunRecord | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return RunRecord(
            run_id=row["run_id"],
            request=SchedulingRequest.model_validate_json(row["request_json"]),
            status=RunStatus(row["status"]),
            response=SchedulingResponse.model_validate_json(row["response_json"]) if row["response_json"] else None,
        )

    def list_runs(self) -> list[RunRecord]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY created_at").fetchall()
        return [
            RunRecord(
                run_id=row["run_id"],
                request=SchedulingRequest.model_validate_json(row["request_json"]),
                status=RunStatus(row["status"]),
                response=SchedulingResponse.model_validate_json(row["response_json"]) if row["response_json"] else None,
            )
            for row in rows
        ]

    @staticmethod
    def _draft_from_row(row: sqlite3.Row) -> DraftRecord:
        return DraftRecord(
            draft_id=row["draft_id"],
            material_id=row["material_id"],
            scheduled_time=row["scheduled_time"],
            schedule_scope=row["schedule_scope"],
            status=row["status"],
            idempotency_key=row["idempotency_key"],
        )
