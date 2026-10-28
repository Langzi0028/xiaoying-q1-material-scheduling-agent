# 02 Solution

## 运行链路

```text
find_existing_draft
-> load_material
-> review_material
-> derive_legal_actions
-> decide_next_action
-> validate_action
-> check_requested_slot / find_alternatives / request_confirmation / save_draft
-> finalize
```

模型决策遵循以下安全闭环：

```text
模型在 legal_actions 中选择动作
-> 调用业务工具
-> 工具结果更新 LangGraph state
-> 模型根据新的 state 选择下一动作或结束
```

`legal_actions` 由确定性代码生成，`validate_action` 会拒绝不在允许集合中的模型输出。模型不能发布、不能直接访问 SQLite、也不能覆盖确认边界。

## 动态决策与确认

- 目标时段可用：模型可选择保存草稿。
- 目标时段冲突：模型根据冲突工具结果选择查询替代时段。
- 找到替代时段：模型选择请求确认，LangGraph `interrupt()` 暂停执行。
- 用户确认后：同一 `thread_id` 经 SQLite checkpoint 恢复；Guard 复核候选时段和确认状态后才允许保存。
- 候选在确认期间失效：工具重新查询并再次请求确认，而不是静默保存冲突时段。

真实在线路径 Trace：[`examples/06-live-llm-conflict-flow.md`](../examples/06-live-llm-conflict-flow.md)。

## 安全边界

- `drafts.status` 只允许 `draft`。
- SQLite 使用 `UNIQUE(idempotency_key)` 防重复，使用 `UNIQUE(schedule_scope, scheduled_time)` 防同范围同一时段冲突。
- 所有时间统一规范化为 `Asia/Shanghai` 的 ISO 秒精度。
- 草稿保存前 Guard 检查审核、候选时段、用户确认和时段可用性。

## 执行上限

每次图执行有 `max_steps` 参数，默认 `24`，CLI 可通过 `--max-steps` 覆盖。每个业务节点增加 `execution_steps`；达到上限后流程返回：

```json
{
  "execution_status": "incomplete",
  "error_code": "EXECUTION_LIMIT_REACHED",
  "draft_save_status": "not_attempted"
}
```

该路径由 `tests/test_execution_limit.py` 覆盖，保证系统不会无限循环或将未完成状态伪装为成功。

## 框架版本与职责

| 组件 | 版本约束 | 职责 |
| --- | --- | --- |
| LangGraph | `>=1.2.5,<1.3` | 状态图、条件路由、interrupt/resume、SQLite checkpoint。|
| LangChain OpenAI | `>=1.1.14,<2.0` | OpenAI 兼容在线模型客户端，返回受限 JSON 决策。|
| Pydantic | `>=2.10,<3.0` | 输入、输出和模型决策的结构化验证。|
| SQLite | Python `sqlite3` | 草稿、运行记录、素材、时段和 checkpoint 持久化。|
| Typer | `>=0.15,<1.0` | 根 `main.py` 使用的 CLI。|

项目遵循本仓库统一考试约定，采用 `main.py + material_scheduler/` 根包 layout，而不是外部示例中的 `src/` layout；两者职责等价，但当前结构可直接从题目根目录运行。
