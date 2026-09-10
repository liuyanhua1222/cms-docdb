# 公共参数

> 旧条款「命令只含业务参数 / 不得传入 AppKey」已废止。

所有业务脚本（含路由辅助脚本）都支持非必填参数：

```text
--app-key APP_KEY
```

含义：当前用户的企业知识库 AppKey（也即玄关开放平台个人 AppKey）。

- 若当前用户的上下文或记忆中已有明确可用、明确属于当前用户的**原始** AppKey，调用脚本时**必须只通过** `--app-key` 传入。
- 没有则省略，由脚本自行获取；不得猜测、拼接或使用其他用户的 AppKey。
- AI **不得**在 Shell 命令前缀、命令正文或工具环境字段中设置鉴权环境变量（至少包括 `XG_OPENAPI_APP_KEY`），也不得从历史工具调用、历史命令、日志或错误信息中复制 AppKey。
- `***`、包含连续三个或更多 `*` 的值、`REDACTED`、`MASKED`、`[REDACTED_APP_KEY]`、`<APP_KEY>`、`<当前用户AppKey>` 等脱敏或占位值不得传入。
- AppKey 不是普通业务内容，不得写入草稿、正文、附件、业务 JSON 或面向用户的结果。
- 若脚本返回 `AUTH_CONTEXT_MISSING`：告知用户未获取到企业知识库 AppKey，请提供或完成配置后重试。
- 若脚本返回 `AUTH_CONTEXT_REDACTED`：请用户重新提供原始 AppKey，不得复用历史命令或日志中的值。
- `--dry-run` 不发起真实请求，可不传 AppKey。
- 参数顺序不是来源优先级；最终用哪一个由脚本决定。

上下文已有原始 AppKey 时的示例（`<当前用户AppKey>` 仅为占位示意，不可原样传入；须替换为真实原始值）：

```bash
python3 -B <skill-dir>/scripts/browse/get-personal-project-id.py --app-key "<当前用户AppKey>"
```
