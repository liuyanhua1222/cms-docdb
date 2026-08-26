# 速查：常用 openapi_skill_exec 调用

> 强制：`skillCode` 恒为 `cms-docdb`；只传业务 argv；禁止 appKey / 脚本路径 / 标准 exec。`retryable: false` 立即停止。

## browse

```json
{"skillCode":"cms-docdb","toolName":"get-app-list","argv":[]}
{"skillCode":"cms-docdb","toolName":"get-uploadable-list","argv":["--app-code","kz_knowledge_base"]}
{"skillCode":"cms-docdb","toolName":"get-project-list","argv":["--app-code","kz_knowledge_base"]}
{"skillCode":"cms-docdb","toolName":"browse","argv":["0"]}
{"skillCode":"cms-docdb","toolName":"folder-navigator","argv":["--project-id","10001","--folder-name","产品资料"]}
{"skillCode":"cms-docdb","toolName":"folder-navigator","argv":["--project-id","10001","--folder-path","产品资料/慷彼申"]}
```

## query

```json
{"skillCode":"cms-docdb","toolName":"search","argv":["合同","--project-id","10001"]}
{"skillCode":"cms-docdb","toolName":"get-file-content","argv":["12345"]}
{"skillCode":"cms-docdb","toolName":"get-full-content","argv":["12345"]}
{"skillCode":"cms-docdb","toolName":"get-download-info","argv":["12345"]}
```

## upload / manage / delete（写入须确认）

```json
{"skillCode":"cms-docdb","toolName":"create-folder","argv":["0","新建目录","--project-id","10001","--dry-run"]}
{"skillCode":"cms-docdb","toolName":"upload-content","argv":["内容","报告.md","--project-id","10001","--confirm","YES"]}
{"skillCode":"cms-docdb","toolName":"delete-file","argv":["12345","--confirm","YES"]}
{"skillCode":"cms-docdb","toolName":"move-file","argv":["12345","--target-parent-id","0","--confirm","YES"]}
```

## 失败处理

| 现象 | 做法 |
|------|------|
| `retryable: false` / `OPENAPI_SKILL_TOOL_NOT_FOUND` | 停止 |
| 鉴权失败 / 401 | 返回对话；不换 Key；不改 exec |
| 缺业务参数 | 按 stderr 中文 hint 补齐后重试同一 toolName |

详见各模块 `references/*/README.md` 与根目录 `SKILL.md`。
