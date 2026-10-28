from ..models import DraftSaveResult
from ..storage.repositories import Repository


class DraftTool:
    def __init__(self, repository: Repository, *, fail_save: bool = False) -> None:
        self.repository = repository
        self.fail_save = fail_save

    def save_draft(
        self,
        *,
        material_id: str,
        selected_time: str,
        schedule_scope: str,
        idempotency_key: str,
    ) -> DraftSaveResult:
        return self.repository.create_or_get_draft(
            material_id=material_id,
            scheduled_time=selected_time,
            schedule_scope=schedule_scope,
            idempotency_key=idempotency_key,
            fail_save=self.fail_save,
        )
