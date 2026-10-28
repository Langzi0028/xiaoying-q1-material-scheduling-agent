# 05 Retrospective

## 实际投入

- 实际投入时间：约 1 小时。

## 最难问题

1. 在“模型可自主调整下一步”与“模型绝不能越权发布或绕过硬性确认”之间建立清晰边界。
2. 保证相同请求重复提交时，不会先把自己的草稿误判为时段冲突。
3. 处理替代时段在用户确认期间被其他草稿占用的情况，要求重新确认而非静默保存。
4. 让 OpenAI 兼容网关的真实模型调用使用稳定的 JSON 字符串消息和结构化解析，避免兼容层对 dict content 的校验失败。

## 学习收获

- LangGraph 的 `interrupt/resume` 与 SQLite checkpoint 能自然表达“用户确认后继续”的 Agent 状态。
- LLM 最适合放在受限的决策层；权限、写入和幂等必须由 Guard 和数据库强制执行。
- 真实 Trace 与 examples 是笔试交付的一部分，不能只依赖单元测试或截图。

## 未完成与限制

- 未接真实内容平台、真实审核服务和真实发布接口；这是有意的安全边界。
- 未实现 HTTP API、GUI、多租户或权限系统，避免超出题目核心范围。
- 在线 LLM 结果仍可能随模型提供方波动，但动作会被 `legal_actions` 和 Guard 约束。

## 后续计划

1. 接入真实素材库和排期系统的只读查询工具。
2. 为替代时段加入优先级、容量和内容渠道策略。
3. 在不改变草稿/确认边界的前提下增加 HTTP API 或运营界面。
4. 在 GitHub 提交前运行 `python scripts/generate_examples.py`、`python scripts/record_live_llm_evidence.py`、`python -m pytest -v` 并记录最终 commit SHA。
