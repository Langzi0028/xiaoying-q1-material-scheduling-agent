from ..enums import ReviewStatus
from ..models import Material, ReviewResult


class RuleTool:
    def check_rules(self, material: Material) -> ReviewResult:
        missing_fields = [
            field_name
            for field_name, value in {"copyright_status": material.copyright_status}.items()
            if value in (None, "")
        ]
        if missing_fields:
            return ReviewResult(status=ReviewStatus.NEEDS_INFO, missing_fields=missing_fields)
        if material.content_risk:
            return ReviewResult(status=ReviewStatus.BLOCKED, risk_reasons=[material.content_risk])
        return ReviewResult(status=ReviewStatus.APPROVED)
