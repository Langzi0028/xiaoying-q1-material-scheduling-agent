# 示例 5：真实 LLM 受限决策

## 输入

```json
{
  "legal_actions": [
    "REQUEST_CONFIRMATION",
    "RETURN_RESULT"
  ],
  "state": {
    "material_id": "M01",
    "requested_time": "2026-10-28T18:00:00+08:00",
    "requested_slot_available": false,
    "offered_alternatives": [
      "2026-10-28T19:00:00+08:00"
    ],
    "confirmation_status": "pending"
  }
}
```

## 实际输出

```json
{
  "action": "REQUEST_CONFIRMATION",
  "source": "live_llm",
  "reason": "The requested time is unavailable; confirmation is needed to schedule the offered alternative at 2026-10-28T19:00:00+08:00."
}
```

## 运行 Trace

```json
[
  {
    "node": "decide_next_action",
    "source": "live_llm",
    "validated_action": "REQUEST_CONFIRMATION"
  }
]
```

## 验证结论

本例由本地 `.env` 中配置的 OpenAI 兼容模型实际返回。记录不包含 `LLM_BASE_URL`、`LLM_API_KEY` 或完整请求头。模型输出只能来自传入的 `legal_actions`，随后仍需由 Guard、时段工具和草稿存储约束执行。
