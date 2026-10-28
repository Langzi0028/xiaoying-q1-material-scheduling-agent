# 示例 8：真实 LLM 驱动的正常保存路径

## 输入

```json
{
  "request_id": "live-llm-normal",
  "material_id": "M02",
  "requested_time": "2026-10-28T20:00:00+08:00",
  "time_requirement_type": "preferred",
  "schedule_scope": "main",
  "idempotency_key": "29f0f5fe964c129b2030ba953e2c2cff5fbebd02b63d7aa5d3a4a59d692b6e63"
}
```

## 实际输出

```json
{
  "run_id": "live-llm-normal",
  "material_id": "M02",
  "review_status": "approved",
  "risk_reasons": [],
  "missing_fields": [],
  "requested_time": "2026-10-28T20:00:00+08:00",
  "suggested_time": "2026-10-28T20:00:00+08:00",
  "confirmation_status": "not_required",
  "pending_confirmation": [],
  "draft_save_status": "saved",
  "draft_id": "draft_e3db6939bc72",
  "error_code": null,
  "execution_status": "completed",
  "message": "排期草稿已保存，尚未发布。"
}
```

## 运行 Trace

```json
[
  {
    "node": "find_existing_draft",
    "update": {}
  },
  {
    "node": "load_material",
    "update": {
      "material": {
        "material_id": "M02",
        "title": "品牌花絮",
        "material_type": "video",
        "copyright_status": "cleared",
        "content_risk": null,
        "schedule_scope": "main"
      }
    }
  },
  {
    "node": "review_material",
    "update": {
      "review_status": "approved",
      "risk_reasons": [],
      "missing_fields": []
    }
  },
  {
    "node": "derive_legal_actions",
    "update": {
      "legal_actions": [
        "CHECK_REQUESTED_SLOT"
      ]
    }
  },
  {
    "node": "decide_next_action",
    "update": {
      "proposed_action": "CHECK_REQUESTED_SLOT",
      "decision_source": "live_llm",
      "decision_reason": "The requested time slot availability has not yet been checked."
    }
  },
  {
    "node": "validate_action",
    "update": {
      "validated_action": "CHECK_REQUESTED_SLOT"
    }
  },
  {
    "node": "check_requested_slot",
    "update": {
      "requested_slot_available": true,
      "conflicts": [],
      "selected_time": "2026-10-28T20:00:00+08:00",
      "suggested_time": "2026-10-28T20:00:00+08:00"
    }
  },
  {
    "node": "derive_legal_actions",
    "update": {
      "legal_actions": [
        "SAVE_DRAFT"
      ]
    }
  },
  {
    "node": "decide_next_action",
    "update": {
      "proposed_action": "SAVE_DRAFT",
      "decision_source": "live_llm",
      "decision_reason": "The material is approved and the requested time slot is available, so save the schedule as a draft pending confirmation."
    }
  },
  {
    "node": "validate_action",
    "update": {
      "validated_action": "SAVE_DRAFT"
    }
  },
  {
    "node": "validate_before_save",
    "update": {}
  },
  {
    "node": "save_draft",
    "update": {
      "draft_save_status": "saved",
      "draft_id": "draft_e3db6939bc72",
      "selected_time": "2026-10-28T20:00:00+08:00",
      "error_code": null,
      "error_message": null
    }
  },
  {
    "node": "finalize",
    "update": {
      "draft_save_status": "saved",
      "confirmation_status": "not_required",
      "final_response": {
        "run_id": "live-llm-normal",
        "material_id": "M02",
        "review_status": "approved",
        "risk_reasons": [],
        "missing_fields": [],
        "requested_time": "2026-10-28T20:00:00+08:00",
        "suggested_time": "2026-10-28T20:00:00+08:00",
        "confirmation_status": "not_required",
        "pending_confirmation": [],
        "draft_save_status": "saved",
        "draft_id": "draft_e3db6939bc72",
        "error_code": null,
        "execution_status": "completed",
        "message": "排期草稿已保存，尚未发布。"
      }
    }
  }
]
```

## 验证结论

真实在线 LLM 基于审核通过和目标时段可用的工具结果，选择查询目标时段并随后选择保存草稿。Trace 中多个 `decide_next_action` 节点的 `decision_source` 为 `live_llm`。最终结果为 `saved`，但状态仍为草稿，文案明确“尚未发布”。
