from dataclasses import dataclass


@dataclass(frozen=True)
class FailureInjection:
    fail_draft_save: bool = False
