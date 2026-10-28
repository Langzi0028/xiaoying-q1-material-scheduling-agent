# 示例 4：草稿保存失败

## 输入

```json
{
  "request_id": "evidence-M02-2026-10-28T22:00:00+08:00",
  "material_id": "M02",
  "requested_time": "2026-10-28T22:00:00+08:00",
  "time_requirement_type": "preferred",
  "schedule_scope": "main",
  "idempotency_key": "73882fbe3c3849f4d5e8b5bad21f6bf046a9aeb400b6a8e8bca74c9a1ed0dc56"
}
```

## 实际输出

```json
{
  "run_id": "example-save-failure",
  "material_id": "M02",
  "review_status": "approved",
  "risk_reasons": [],
  "missing_fields": [],
  "requested_time": "2026-10-28T22:00:00+08:00",
  "suggested_time": "2026-10-28T22:00:00+08:00",
  "confirmation_status": "not_required",
  "pending_confirmation": [],
  "draft_save_status": "failed",
  "draft_id": null,
  "error_code": "SAVE_FAILED",
  "execution_status": "completed",
  "message": "草稿保存失败：模拟数据库写入异常；未创建草稿，尚未发布。"
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
      "selected_time": "2026-10-28T22:00:00+08:00",
      "suggested_time": "2026-10-28T22:00:00+08:00"
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
      "draft_save_status": "failed",
      "draft_id": null,
      "selected_time": "2026-10-28T22:00:00+08:00",
      "error_code": "SAVE_FAILED",
      "error_message": "模拟数据库写入异常"
    }
  },
  {
    "node": "finalize",
    "update": {
      "draft_save_status": "failed",
      "confirmation_status": "not_required",
      "final_response": {
        "run_id": "example-save-failure",
        "material_id": "M02",
        "review_status": "approved",
        "risk_reasons": [],
        "missing_fields": [],
        "requested_time": "2026-10-28T22:00:00+08:00",
        "suggested_time": "2026-10-28T22:00:00+08:00",
        "confirmation_status": "not_required",
        "pending_confirmation": [],
        "draft_save_status": "failed",
        "draft_id": null,
        "error_code": "SAVE_FAILED",
        "execution_status": "completed",
        "message": "草稿保存失败：模拟数据库写入异常；未创建草稿，尚未发布。"
      }
    }
  }
]
```

## 验证结论

保存工具注入失败，返回 `failed` 和 `SAVE_FAILED`；不会声称草稿已保存或发布成功。
