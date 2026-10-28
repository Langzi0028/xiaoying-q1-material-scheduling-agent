# 面试演示脚本

所有命令都在 `xiaoying-q1-material-scheduling-agent` 目录执行。建议使用一个新的数据库文件，保证演示数据隔离。

```powershell
$db = "data/interview-demo.db"
Remove-Item $db -ErrorAction SilentlyContinue -Force
python main.py demo seed --database $db
```

## 1. 正常排期

```powershell
python main.py demo normal --database $db
```

预期：M02 审核通过，20:00 可用，输出 `draft_save_status: saved` 和“草稿已保存，尚未发布”。

## 2. 题目参考案例：冲突调整与确认边界

```powershell
python main.py demo conflict --database $db
python main.py list-runs --database $db
```

预期：M01 的 18:00 已被占用，Agent 建议 19:00，运行状态是 `waiting_confirmation`，且 `draft_save_status` 为 `not_attempted`。此时数据库没有 M01 草稿，输出明确“尚未发布”。

从 `list-runs` 复制该案例的 `run_id`：

```powershell
python main.py resume `
  --run-id RUN_ID `
  --confirm `
  --time "2026-10-28T19:00:00+08:00" `
  --database $db
```

预期：同一个 LangGraph thread 从 checkpoint 恢复，保存 19:00 的一份草稿，仍只表述“尚未发布”。

## 3. 信息缺失与规则风险

```powershell
python main.py demo missing-info --database $db
python main.py demo rule-risk --database $db
```

预期：M03 返回 `needs_info` 和 `copyright_status`；M04 返回 `blocked` 和 `sensitive_content`；两者都不保存草稿。

## 4. 重复提交

```powershell
python main.py demo duplicate --database $db
```

预期：相同请求第二次返回 `duplicate_reused`，数据库只有一份对应草稿，不会因自身时段占用而改推其他时间。

## 5. 保存失败

```powershell
python main.py demo save-failure --database $db
```

预期：输出 `draft_save_status: failed` 和“草稿保存失败”；不能出现“草稿已保存”或任何发布成功描述。

## 6. 回归测试

```powershell
python -m pytest -v
```

当前自动化验证使用真实 SQLite、LangGraph 和 CLI。真实 LLM 只有在配置有效的环境变量后才运行；未配置密钥时只能报告离线受限决策验证，不能声称模型调用已验证。

## 7. 执行上限

```powershell
python main.py schedule `
  --material-id M02 `
  --time "2026-10-28T20:00:00+08:00" `
  --max-steps 1 `
  --database $db
```

预期：返回 `execution_status: incomplete`、`EXECUTION_LIMIT_REACHED` 和 `draft_save_status: not_attempted`；不会创建草稿，更不会发布。
