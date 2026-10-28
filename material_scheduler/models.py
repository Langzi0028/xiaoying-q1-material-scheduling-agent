from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import (
    ConfirmationStatus,
    DraftSaveStatus,
    ErrorCode,
    ReviewStatus,
    RunStatus,
    TimeRequirementType,
)

SHANGHAI = ZoneInfo("Asia/Shanghai")


def canonicalize_time(value: str | datetime) -> str:
    """Return an offset-aware timestamp in the only storage representation."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("requested_time must include a timezone offset")
    return parsed.astimezone(SHANGHAI).replace(microsecond=0).isoformat()


def build_idempotency_key(
    material_id: str,
    requested_time: str,
    time_requirement_type: TimeRequirementType,
    schedule_scope: str,
) -> str:
    source = "|".join(
        (
            material_id.strip(),
            requested_time,
            time_requirement_type.value,
            schedule_scope.strip(),
            "schedule_draft_v1",
        )
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


class SchedulingRequest(BaseModel):
    request_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    requested_time: str
    time_requirement_type: TimeRequirementType
    schedule_scope: str = Field(default="main", min_length=1)
    idempotency_key: str = ""

    @field_validator("requested_time", mode="before")
    @classmethod
    def normalize_requested_time(cls, value: str | datetime) -> str:
        return canonicalize_time(value)

    @model_validator(mode="after")
    def set_idempotency_key(self) -> SchedulingRequest:
        self.idempotency_key = build_idempotency_key(
            self.material_id,
            self.requested_time,
            self.time_requirement_type,
            self.schedule_scope,
        )
        return self


class Material(BaseModel):
    material_id: str
    title: str
    material_type: str
    copyright_status: str | None = None
    content_risk: str | None = None
    schedule_scope: str = "main"


class ReviewResult(BaseModel):
    status: ReviewStatus
    risk_reasons: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class SlotCheckResult(BaseModel):
    requested_time: str
    available: bool
    conflicts: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class DraftRecord(BaseModel):
    draft_id: str
    material_id: str
    scheduled_time: str
    schedule_scope: str
    status: str = "draft"
    idempotency_key: str


class DraftSaveResult(BaseModel):
    status: DraftSaveStatus
    draft: DraftRecord | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None


class ConfirmationInput(BaseModel):
    confirmed: bool
    selected_time: str | None = None

    @field_validator("selected_time", mode="before")
    @classmethod
    def normalize_selected_time(cls, value: str | datetime | None) -> str | None:
        return canonicalize_time(value) if value is not None else None


class SchedulingResponse(BaseModel):
    run_id: str
    material_id: str
    review_status: ReviewStatus | None = None
    risk_reasons: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    requested_time: str
    suggested_time: str | None = None
    confirmation_status: ConfirmationStatus = ConfirmationStatus.NOT_REQUIRED
    pending_confirmation: list[str] = Field(default_factory=list)
    draft_save_status: DraftSaveStatus = DraftSaveStatus.NOT_ATTEMPTED
    draft_id: str | None = None
    error_code: ErrorCode | None = None
    execution_status: str = "completed"
    message: str


class RunRecord(BaseModel):
    run_id: str
    request: SchedulingRequest
    status: RunStatus
    response: SchedulingResponse | None = None
