# 示例 3：冲突调整、用户确认与重复提交

## 输入

```json
{
  "request_id": "evidence-M01-2026-10-28T18:00:00+08:00",
  "material_id": "M01",
  "requested_time": "2026-10-28T18:00:00+08:00",
  "time_requirement_type": "preferred",
  "schedule_scope": "main",
  "idempotency_key": "a3aaec5d9640d65d1698dc5ea6949935b4c0507dd820193f102cbf533ef32625"
}
```

## 实际输出

```json
{
  "first_run": {
    "run_status": "waiting_confirmation",
    "message": "目标时段冲突，请确认替代时段；尚未保存草稿，尚未发布。",
    "requested_time": "2026-10-28T18:00:00+08:00",
    "conflicts": [
      "18:00 已被既有排期占用"
    ],
    "suggested_time": "2026-10-28T19:00:00+08:00",
    "draft_save_status": "not_attempted"
  },
  "confirmed_run": {
    "run_id": "example-conflict-confirm",
    "material_id": "M01",
    "review_status": "approved",
    "risk_reasons": [],
    "missing_fields": [],
    "requested_time": "2026-10-28T18:00:00+08:00",
    "suggested_time": "2026-10-28T19:00:00+08:00",
    "confirmation_status": "confirmed",
    "pending_confirmation": [],
    "draft_save_status": "saved",
    "draft_id": "draft_c45bffccd150",
    "error_code": null,
    "execution_status": "completed",
    "message": "排期草稿已保存，尚未发布。"
  },
  "duplicate_run": {
    "run_id": "example-conflict-duplicate",
    "material_id": "M01",
    "review_status": "approved",
    "risk_reasons": [],
    "missing_fields": [],
    "requested_time": "2026-10-28T18:00:00+08:00",
    "suggested_time": "2026-10-28T19:00:00+08:00",
    "confirmation_status": "confirmed",
    "pending_confirmation": [],
    "draft_save_status": "duplicate_reused",
    "draft_id": "draft_c45bffccd150",
    "error_code": null,
    "execution_status": "completed",
    "message": "已复用已有排期草稿，尚未发布。"
  }
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
        "material_id": "M01",
        "title": "新品预告短片",
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
      "requested_slot_available": false,
      "conflicts": [
        "18:00 已被既有排期占用"
      ]
    }
  },
  {
    "node": "derive_legal_actions",
    "update": {
      "legal_actions": [
        "CHECK_ALTERNATIVES"
      ]
    }
  },
  {
    "node": "decide_next_action",
    "update": {
      "proposed_action": "CHECK_ALTERNATIVES",
      "decision_source": "injected_test_engine"
    }
  },
  {
    "node": "validate_action",
    "update": {
      "validated_action": "CHECK_ALTERNATIVES"
    }
  },
  {
    "node": "find_alternatives",
    "update": {
      "offered_alternatives": [
        "2026-10-28T19:00:00+08:00"
      ],
      "suggested_time": "2026-10-28T19:00:00+08:00",
      "needs_confirmation": true
    }
  },
  {
    "node": "derive_legal_actions",
    "update": {
      "legal_actions": [
        "REQUEST_CONFIRMATION"
      ]
    }
  },
  {
    "node": "decide_next_action",
    "update": {
      "proposed_action": "REQUEST_CONFIRMATION",
      "decision_source": "injected_test_engine"
    }
  },
  {
    "node": "validate_action",
    "update": {
      "validated_action": "REQUEST_CONFIRMATION"
    }
  },
  {
    "node": "request_confirmation",
    "update": {
      "status": "interrupt_requested",
      "payload": {
        "message": "目标时段冲突，请确认替代时段；尚未保存草稿，尚未发布。",
        "requested_time": "2026-10-28T18:00:00+08:00",
        "conflicts": [
          "18:00 已被既有排期占用"
        ],
        "alternatives": [
          "2026-10-28T19:00:00+08:00"
        ]
      }
    }
  },
  {
    "node": "request_confirmation",
    "update": {
      "status": "interrupt_requested",
      "payload": {
        "message": "目标时段冲突，请确认替代时段；尚未保存草稿，尚未发布。",
        "requested_time": "2026-10-28T18:00:00+08:00",
        "conflicts": [
          "18:00 已被既有排期占用"
        ],
        "alternatives": [
          "2026-10-28T19:00:00+08:00"
        ]
      }
    }
  },
  {
    "node": "request_confirmation",
    "update": {
      "confirmation_status": "confirmed",
      "needs_confirmation": false,
      "selected_time": "2026-10-28T19:00:00+08:00"
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
      "draft_id": "draft_c45bffccd150",
      "selected_time": "2026-10-28T19:00:00+08:00",
      "error_code": null,
      "error_message": null
    }
  },
  {
    "node": "finalize",
    "update": {
      "draft_save_status": "saved",
      "confirmation_status": "confirmed",
      "final_response": {
        "run_id": "example-conflict-confirm",
        "material_id": "M01",
        "review_status": "approved",
        "risk_reasons": [],
        "missing_fields": [],
        "requested_time": "2026-10-28T18:00:00+08:00",
        "suggested_time": "2026-10-28T19:00:00+08:00",
        "confirmation_status": "confirmed",
        "pending_confirmation": [],
        "draft_save_status": "saved",
        "draft_id": "draft_c45bffccd150",
        "error_code": null,
        "execution_status": "completed",
        "message": "排期草稿已保存，尚未发布。"
      }
    }
  },
  {
    "node": "find_existing_draft",
    "update": {
      "review_status": "approved",
      "draft_save_status": "duplicate_reused",
      "draft_id": "draft_c45bffccd150",
      "selected_time": "2026-10-28T19:00:00+08:00",
      "suggested_time": "2026-10-28T19:00:00+08:00",
      "confirmation_status": "confirmed"
    }
  },
  {
    "node": "finalize",
    "update": {
      "draft_save_status": "duplicate_reused",
      "confirmation_status": "confirmed",
      "final_response": {
        "run_id": "example-conflict-duplicate",
        "material_id": "M01",
        "review_status": "approved",
        "risk_reasons": [],
        "missing_fields": [],
        "requested_time": "2026-10-28T18:00:00+08:00",
        "suggested_time": "2026-10-28T19:00:00+08:00",
        "confirmation_status": "confirmed",
        "pending_confirmation": [],
        "draft_save_status": "duplicate_reused",
        "draft_id": "draft_c45bffccd150",
        "error_code": null,
        "execution_status": "completed",
        "message": "已复用已有排期草稿，尚未发布。"
      }
    }
  }
]
```

## 验证结论

首次运行因 18:00 占用而中断，建议 19:00 并等待确认。确认后只保存草稿。随后以相同请求重新运行，`duplicate_run` 返回 `duplicate_reused`，复用同一草稿。
