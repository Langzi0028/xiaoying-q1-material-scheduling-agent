from enum import StrEnum


class ReviewStatus(StrEnum):
    APPROVED = "approved"
    NEEDS_INFO = "needs_info"
    BLOCKED = "blocked"


class ConfirmationStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DraftSaveStatus(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    SAVED = "saved"
    DUPLICATE_REUSED = "duplicate_reused"
    FAILED = "failed"


class TimeRequirementType(StrEnum):
    HARD = "hard"
    PREFERRED = "preferred"
    FLEXIBLE = "flexible"


class RunStatus(StrEnum):
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorCode(StrEnum):
    MATERIAL_NOT_FOUND = "MATERIAL_NOT_FOUND"
    MISSING_METADATA = "MISSING_METADATA"
    RULE_BLOCKED = "RULE_BLOCKED"
    NO_SLOT_AVAILABLE = "NO_SLOT_AVAILABLE"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    INVALID_CONFIRMATION = "INVALID_CONFIRMATION"
    HARD_TIME_CHANGE_FORBIDDEN = "HARD_TIME_CHANGE_FORBIDDEN"
    SLOT_CONFLICT = "SLOT_CONFLICT"
    SAVE_FAILED = "SAVE_FAILED"
    DECISION_REJECTED = "DECISION_REJECTED"
    EXECUTION_LIMIT_REACHED = "EXECUTION_LIMIT_REACHED"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
