# 公共参数

> 旧条款「命令只含业务参数 / 不得传入 AppKey」已废止。

所有业务脚本（含路由辅助脚本）都支持非必填参数：

```text
--app-key APP_KEY
```

含义：当前用户的企业知识库 AppKey。

- 若当前用户的上下文或记忆中已有明确可用、明确属于当前用户的 AppKey，调用脚本时可以传入。
- 没有则省略，由脚本自行获取。
- 不得猜测、拼接或使用其他用户的 AppKey。
- AppKey 不是普通业务内容，不得写入草稿、正文、附件、业务 JSON 或面向用户的结果。
- `--dry-run` 不发起真实请求，可不传 AppKey。
- 参数顺序不是来源优先级；最终用哪一个由脚本决定。

上下文已有 AppKey 时的示例：

```bash
python3 -B <skill-dir>/scripts/browse/get-personal-project-id.py --app-key "<当前用户AppKey>"
```
