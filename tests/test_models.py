from datetime import datetime

import pytest
from pydantic import ValidationError

from material_scheduler.enums import TimeRequirementType
from material_scheduler.models import SchedulingRequest, canonicalize_time


def test_request_normalizes_timestamp_to_shanghai_and_builds_stable_fingerprint() -> None:
    utc_request = SchedulingRequest(
        request_id="req-utc",
        material_id="M01",
        requested_time="2026-10-28T10:00:00Z",
        time_requirement_type=TimeRequirementType.PREFERRED,
        schedule_scope="main",
    )
    shanghai_request = SchedulingRequest(
        request_id="req-shanghai",
        material_id="M01",
        requested_time="2026-10-28T18:00:00+08:00",
        time_requirement_type=TimeRequirementType.PREFERRED,
        schedule_scope="main",
    )

    assert utc_request.requested_time == "2026-10-28T18:00:00+08:00"
    assert utc_request.idempotency_key == shanghai_request.idempotency_key


def test_request_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        SchedulingRequest(
            request_id="req-naive",
            material_id="M01",
            requested_time="2026-10-28T18:00:00",
            time_requirement_type=TimeRequirementType.PREFERRED,
        )


def test_canonicalize_time_returns_iso_seconds() -> None:
    value = canonicalize_time(datetime.fromisoformat("2026-10-28T18:00:12.987654+08:00"))

    assert value == "2026-10-28T18:00:12+08:00"
