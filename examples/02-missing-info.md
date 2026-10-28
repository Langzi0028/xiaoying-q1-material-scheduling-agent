# 示例 2：素材信息不足

## 输入

```json
{
  "request_id": "evidence-M03-2026-10-28T20:00:00+08:00",
  "material_id": "M03",
  "requested_time": "2026-10-28T20:00:00+08:00",
  "time_requirement_type": "preferred",
  "schedule_scope": "main",
  "idempotency_key": "01678f22846265cd8ccf99255265d9649cbb5891acc1cc2308b1f9ca4706e14f"
}
```

## 实际输出

```json
{
  "run_id": "example-missing-info",
  "material_id": "M03",
  "review_status": "needs_info",
  "risk_reasons": [],
  "missing_fields": [
    "copyright_status"
  ],
  "requested_time": "2026-10-28T20:00:00+08:00",
  "suggested_time": null,
  "confirmation_status": "not_required",
  "pending_confirmation": [],
  "draft_save_status": "not_attempted",
  "draft_id": null,
  "error_code": "MISSING_METADATA",
  "execution_status": "completed",
  "message": "素材信息缺失，等待补充；尚未保存草稿，更未发布。"
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
        "material_id": "M03",
        "title": "版权待补充素材",
        "material_type": "image",
        "copyright_status": null,
        "content_risk": null,
        "schedule_scope": "main"
      }
    }
  },
  {
    "node": "review_material",
    "update": {
      "review_status": "needs_info",
      "risk_reasons": [],
      "missing_fields": [
        "copyright_status"
      ],
      "error_code": "MISSING_METADATA",
      "error_message": "素材信息不完整，需要补充后再排期"
    }
  },
  {
    "node": "derive_legal_actions",
    "update": {
      "legal_actions": [
        "RETURN_RESULT"
      ]
    }
  },
  {
    "node": "decide_next_action",
    "update": {
      "proposed_action": "RETURN_RESULT",
      "decision_source": "injected_test_engine"
    }
  },
  {
    "node": "validate_action",
    "update": {
      "validated_action": "RETURN_RESULT"
    }
  },
  {
    "node": "finalize",
    "update": {
      "draft_save_status": "not_attempted",
      "confirmation_status": "not_required",
      "final_response": {
        "run_id": "example-missing-info",
        "material_id": "M03",
        "review_status": "needs_info",
        "risk_reasons": [],
        "missing_fields": [
          "copyright_status"
        ],
        "requested_time": "2026-10-28T20:00:00+08:00",
        "suggested_time": null,
        "confirmation_status": "not_required",
        "pending_confirmation": [],
        "draft_save_status": "not_attempted",
        "draft_id": null,
        "error_code": "MISSING_METADATA",
        "execution_status": "completed",
        "message": "素材信息缺失，等待补充；尚未保存草稿，更未发布。"
      }
    }
  }
]
```

## 验证结论

审核状态为 `needs_info`，指出缺失 `copyright_status`，草稿保存状态为 `not_attempted`。
