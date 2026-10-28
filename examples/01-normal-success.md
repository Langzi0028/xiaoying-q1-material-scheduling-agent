# 示例 1：正常排期并保存草稿

## 输入

```json
{
  "request_id": "evidence-M02-2026-10-28T20:00:00+08:00",
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
  "run_id": "example-normal",
  "material_id": "M02",
  "review_status": "approved",
  "risk_reasons": [],
  "missing_fields": [],
  "requested_time": "2026-10-28T20:00:00+08:00",
  "suggested_time": "2026-10-28T20:00:00+08:00",
  "confirmation_status": "not_required",
  "pending_confirmation": [],
  "draft_save_status": "saved",
  "draft_id": "draft_82ed4885e717",
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
      "decision_source": "injected_test_engine"
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
      "decision_source": "injected_test_engine"
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
      "draft_id": "draft_82ed4885e717",
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
        "run_id": "example-normal",
        "material_id": "M02",
        "review_status": "approved",
        "risk_reasons": [],
        "missing_fields": [],
        "requested_time": "2026-10-28T20:00:00+08:00",
        "suggested_time": "2026-10-28T20:00:00+08:00",
        "confirmation_status": "not_required",
        "pending_confirmation": [],
        "draft_save_status": "saved",
        "draft_id": "draft_82ed4885e717",
        "error_code": null,
        "execution_status": "completed",
        "message": "排期草稿已保存，尚未发布。"
      }
    }
  }
]
```

## 验证结论

审核通过、目标时段可用，保存状态为 `saved`。输出明确为草稿且“尚未发布”。
