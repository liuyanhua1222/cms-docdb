# 速查：常用标准 exec 调用

> 强制：将 `<skill-dir>` 换成本 skill 根目录绝对路径；传业务参数，可选 `--app-key`（旧条款「只传业务参数」已废止，见 `common-params.md`）。缺参按 stderr 中文提示补齐后用同一 python 命令重试。写入须 `--confirm YES`（可先 `--dry-run`）。

## browse

```bash
python3 -B <skill-dir>/scripts/browse/get-app-list.py
python3 -B <skill-dir>/scripts/browse/get-uploadable-list.py --app-code kz_knowledge_base
python3 -B <skill-dir>/scripts/browse/get-project-list.py --app-code kz_knowledge_base
python3 -B <skill-dir>/scripts/browse/get-personal-project-id.py
# 下式为占位示意，不可原样传入；有原始 AppKey 时再附加 --app-key
python3 -B <skill-dir>/scripts/browse/get-personal-project-id.py --app-key "<当前用户AppKey>"
python3 -B <skill-dir>/scripts/browse/get-level1-folders.py --project-id <projectId>
python3 -B <skill-dir>/scripts/browse/browse.py --parent-id 12345
python3 -B <skill-dir>/scripts/browse/resolve-path.py --project-id 10001 --path "产品资料/慷彼申"
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-name "产品资料"
python3 -B <skill-dir>/scripts/folder-navigator.py --project-id 10001 --folder-path "产品资料/慷彼申"
```

## query

```bash
python3 -B <skill-dir>/scripts/query/search.py --name-key "合同" --project-id 10001
python3 -B <skill-dir>/scripts/query/get-file-content.py --file-id 12345
python3 -B <skill-dir>/scripts/query/get-full-content.py --file-id 12345
python3 -B <skill-dir>/scripts/query/get-download-info.py --file-id 12345
```

## upload / manage / delete（写入须确认）

```bash
python3 -B <skill-dir>/scripts/upload/create-folder.py --parent-id 0 --name "新建目录" --project-id 10001 --dry-run
python3 -B <skill-dir>/scripts/upload/upload-content.py --content "内容" --file-name "报告.md" --project-id 10001 --confirm YES
# 虚拟文件：relationTitle 必填（对齐 PC：huiji/notex→name，ai-report→taskName，汇报/任务→main；禁止省略）
python3 -B <skill-dir>/scripts/upload/add-third-file.py --project-id 10001 --file-type huiji --relation-id 987654 --relation-title "纪要" --folder-path "AI慧记" --confirm YES
python3 -B <skill-dir>/scripts/upload/update-file-relation.py --project-id 20001 --parent-file-id 3001 --file-type work_report --relation-id 111 --relation-title "周报" --confirm YES
python3 -B <skill-dir>/scripts/upload/batch-add-file-relation.py --project-id 20001 --file-type huiji --relations-json '[{"relationId":"1","relationTitle":"A"},{"relationId":"2","relationTitle":"B"}]' --confirm YES
python3 -B <skill-dir>/scripts/delete/delete-file.py --file-id 12345 --confirm YES
python3 -B <skill-dir>/scripts/manage/move-file.py --file-id 12345 --target-parent-id 0 --confirm YES
```

## 失败处理

| 现象 | 做法 |
|------|------|
| 脚本公开错误 | 展示给用户；`AUTH_CONTEXT_MISSING` 时请用户提供 AppKey；`AUTH_CONTEXT_REDACTED` 时请重新提供原始值 |
| `AUTH_CONTEXT_MISSING` | 告知未获取到企业知识库 AppKey，请提供或完成配置后重试 |
| `AUTH_CONTEXT_INVALID` | 告知配置值非法，不得自动修剪或换用低优先级参数 |
| `AUTH_CONTEXT_REDACTED` | 请用户重新提供原始 AppKey，不得复用历史命令或日志 |
| 缺业务参数 | 按 stderr 补齐后重试同一命令 |
| 须 `--confirm YES` | 先获用户确认再执行 |

详见各模块 `references/*/README.md` 与根目录 `SKILL.md`。
