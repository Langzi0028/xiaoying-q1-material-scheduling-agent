# 示例 6：真实 LLM 驱动的冲突处理路径

## 输入

```json
{
  "request_id": "live-llm-conflict",
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
  "run_status": "waiting_confirmation",
  "suggested_time": "2026-10-28T19:00:00+08:00",
  "draft_save_status": "not_attempted"
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
      "decision_source": "live_llm",
      "decision_reason": "The requested slot availability has not been checked yet."
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
      "decision_source": "live_llm",
      "decision_reason": "The requested time slot is unavailable, and no alternative slots have been offered yet."
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
      "decision_source": "live_llm",
      "decision_reason": "The requested slot at 2026-10-28T18:00:00+08:00 is unavailable. Please confirm the offered alternative at 2026-10-28T19:00:00+08:00."
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
  }
]
```

## 验证结论

真实在线 LLM 依次基于工具结果选择查目标时段、查替代时段、请求用户确认。Trace 中每个 `decide_next_action` 节点的 `decision_source` 为 `live_llm`。18:00 冲突后推荐 19:00 并中断，未创建草稿；模型不具有发布或直接写库能力。
