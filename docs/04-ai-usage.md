# 04 AI Usage

## AI 协助内容

- 将题目自然语言要求拆解为素材审核、规则检查、时段查询、确认和草稿保存的状态机。
- 生成 LangGraph 节点、SQLite 持久化、CLI、测试用例和验证 Trace 的初稿。
- 协助梳理幂等键、时段唯一约束、确认恢复与保存失败的边界条件。
- 协助生成文档草稿、examples 验证材料和评估索引。

## 人工完成与审核

- 人工完成整体图链路编排审核，以及验证问题设置。
- 人工确认项目保持 draft-only 边界，不接真实发布能力。
- 人工配置真实 LLM 并触发在线受限决策测试。
- 人工检查真实输出、Trace、数据库写入状态、测试结果和提交材料中不包含密钥或网关地址。
- 人工决定采用根目录 `main.py + material_scheduler/` 的统一考试项目布局。

## 证据

- 业务回归测试：`tests/`。
- 真实 LLM 决策：`tests/test_llm_live.py` 和 `examples/05-live-llm-decision.md`。
- 真实 LLM 冲突流程：`examples/06-live-llm-conflict-flow.md`。
- 验收映射：`docs/03-evaluation.md`。

AI 只作为开发协作者；最终业务边界、配置、验证命令和提交内容由人工审核。
