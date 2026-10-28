# 03 Evaluation

本文件是评估入口，汇总验收矩阵、框架职责、命令和限制。

## 实际验证结果

```text
python -m pytest -v
50 passed
```

其中真实在线模型测试为：

```text
tests/test_llm_live.py::test_real_llm_makes_a_constrained_decision
PASSED
```

## 框架与职责摘要

- `LangGraph`：执行状态图、条件路由、确认中断/恢复和 SQLite checkpoint。
- `LangChain OpenAI`：执行真实在线模型的受限动作选择；Guard 仍负责权限与安全边界。
- `SQLite`：保存素材、时段、草稿和运行记录，并用唯一约束保障幂等和排期排他。

完整版本约束与组件责任边界见 [`docs/02-solution.md`](02-solution.md)。

## 证据索引

- 正常排期：[`examples/01-normal-success.md`](../examples/01-normal-success.md)
- 信息不足：[`examples/02-missing-info.md`](../examples/02-missing-info.md)
- M01 冲突、确认与幂等：[`examples/03-conflict-confirm-duplicate.md`](../examples/03-conflict-confirm-duplicate.md)
- 保存失败：[`examples/04-save-failure.md`](../examples/04-save-failure.md)
- 单次真实 LLM 受限决策：[`examples/05-live-llm-decision.md`](../examples/05-live-llm-decision.md)
- 真实 LLM 冲突处理链路：[`examples/06-live-llm-conflict-flow.md`](../examples/06-live-llm-conflict-flow.md)
- 真实 LLM 正常保存链路：[`examples/08-live-llm-normal-flow.md`](../examples/08-live-llm-normal-flow.md)
- 执行上限：[`examples/07-execution-limit.md`](../examples/07-execution-limit.md)

## 失败与限制

- 模型未配置或请求失败时走 deterministic fallback，并将提示写入 stderr；不把 fallback 当作真实模型效果。
- demo 使用本地 SQLite 与合成素材/规则，不接入真实发布平台。
- 执行步骤达到 `max_steps` 后返回 `EXECUTION_LIMIT_REACHED` 和 `incomplete`，不产生草稿。
