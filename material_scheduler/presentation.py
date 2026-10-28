from __future__ import annotations

import json
from typing import Any


def format_result(result: dict[str, Any]) -> str:
    if "__interrupt__" in result:
        interrupt_value = result["__interrupt__"][0].value
        payload = {
            "run_status": "waiting_confirmation",
            "message": interrupt_value["message"],
            "requested_time": interrupt_value["requested_time"],
            "conflicts": interrupt_value["conflicts"],
            "suggested_time": interrupt_value["alternatives"][0] if interrupt_value["alternatives"] else None,
            "draft_save_status": "not_attempted",
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return json.dumps(result.get("final_response", result), ensure_ascii=False, indent=2)
