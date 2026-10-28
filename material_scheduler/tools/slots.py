from datetime import timedelta

from ..models import SlotCheckResult, canonicalize_time
from ..storage.repositories import Repository


class SlotTool:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def check_slot(self, *, schedule_scope: str, requested_time: str) -> SlotCheckResult:
        normalized_time = canonicalize_time(requested_time)
        conflict = self.repository.get_slot_conflict(schedule_scope, normalized_time)
        alternatives = self.find_alternatives(schedule_scope=schedule_scope, requested_time=normalized_time) if conflict else []
        return SlotCheckResult(
            requested_time=normalized_time,
            available=conflict is None,
            conflicts=[conflict] if conflict else [],
            alternatives=alternatives,
        )

    def find_alternatives(self, *, schedule_scope: str, requested_time: str) -> list[str]:
        candidate = canonicalize_time(requested_time)
        from datetime import datetime

        cursor = datetime.fromisoformat(candidate)
        alternatives: list[str] = []
        for hour_offset in range(1, 5):
            proposed = canonicalize_time(cursor + timedelta(hours=hour_offset))
            if self.repository.get_slot_conflict(schedule_scope, proposed) is None:
                alternatives.append(proposed)
            if len(alternatives) == 1:
                break
        return alternatives
