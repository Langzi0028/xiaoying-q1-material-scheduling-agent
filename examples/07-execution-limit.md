# 示例 7：达到执行上限的未完成状态

## 输入

```json
{
  "request_id": "evidence-M02-2026-10-28T20:00:00+08:00",
  "material_id": "M02",
  "requested_time": "2026-10-28T20:00:00+08:00",
  "time_requirement_type": "preferred",
  "schedule_scope": "main",
  "idempotency_key": "29f0f5fe964c129b2030ba953e2c2cff5fbebd02b63d7aa5d3a4a59d692b6e63",
  "max_steps": 1
}
```

## 实际输出

```json
{
  "run_id": "example-execution-limit",
  "material_id": "M02",
  "review_status": null,
  "risk_reasons": [],
  "missing_fields": [],
  "requested_time": "2026-10-28T20:00:00+08:00",
  "suggested_time": null,
  "confirmation_status": "not_required",
  "pending_confirmation": [],
  "draft_save_status": "not_attempted",
  "draft_id": null,
  "error_code": "EXECUTION_LIMIT_REACHED",
  "execution_status": "incomplete",
  "message": "已达到执行步骤上限，未形成草稿，尚未发布。"
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
    "node": "finalize",
    "update": {
      "draft_save_status": "not_attempted",
      "confirmation_status": "not_required",
      "final_response": {
        "run_id": "example-execution-limit",
        "material_id": "M02",
        "review_status": null,
        "risk_reasons": [],
        "missing_fields": [],
        "requested_time": "2026-10-28T20:00:00+08:00",
        "suggested_time": null,
        "confirmation_status": "not_required",
        "pending_confirmation": [],
        "draft_save_status": "not_attempted",
        "draft_id": null,
        "error_code": "EXECUTION_LIMIT_REACHED",
        "execution_status": "incomplete",
        "message": "已达到执行步骤上限，未形成草稿，尚未发布。"
      }
    }
  }
]
```

## 验证结论

流程达到 `max_steps` 后返回 `execution_status: incomplete` 和 `EXECUTION_LIMIT_REACHED`，未创建草稿。
