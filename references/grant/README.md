# grant — 目录授权（t_file_grant）

与 `share` 模块（`t_file_share` 协同分享）不同。被授权人**须为空间成员**；非成员须先 `add-member` 或走协同分享。

**增量语义**：仅影响请求中的用户，不删除他人授权。禁止全量 replace。

## 权限策略

| 阶段 | 规则 |
|---|---|
| 新授权 | 必须指定 permissions；服务端合并 `read+preview` + 指定项（不含 `fileshare`） |
| 编辑减权 | `read` 兜底；`preview`/`download` 等可单独去掉 → `strip-grant-permissions.py` |
| 整单收回 | `revoke-file-grants.py`（勿用于单项减权） |

凭证以命令行 `--appkey` 传入，值取自会话用户消息上下文的 `CMS_CWORK_APPKEY`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

## 脚本清单

| 脚本 | 接口 |
|------|------|
| `scripts/grant/upsert-file-grants.py` | `POST .../fileGrant/upsertGrants` |
| `scripts/grant/get-file-grants.py` | `GET .../fileGrant/getGrants` |
| `scripts/grant/strip-grant-permissions.py` | 单项减权（内部 upsert） |
| `scripts/grant/revoke-file-grants.py` | `POST .../fileGrant/revokeGrants`（整单收回） |
| `scripts/admin/is-project-member.py` | `GET .../admin/isProjectMember`（授权前自检） |

不可授予 `admin`、`permmanage`。

## 示例

**重要说明**：以下示例使用相对路径以便阅读，实际执行时必须替换为绝对路径。例如：
- 文档示例：`python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 123456`
- 实际执行：`python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 123456`（将 `<skill-dir>` 换成 skill 根目录绝对路径）

禁止使用 `cd`、`&&`、管道等 shell 构造。每个脚本必须在单独的命令中使用绝对路径执行。

```bash
python3 -B <skill-dir>/scripts/admin/is-project-member.py 888
python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 123456 --emp-id 10002 --permissions "read,preview,download" --dry-run
python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 123456 --emp-id 10002 --permissions "download" --confirm YES
python3 -B <skill-dir>/scripts/grant/get-file-grants.py 123456
python3 -B <skill-dir>/scripts/grant/strip-grant-permissions.py 123456 --emp-id 10002 --remove download --confirm YES
python3 -B <skill-dir>/scripts/grant/revoke-file-grants.py 123456 --emp-ids 10002 --confirm YES
```

写入类须先获用户确认，再带 `--confirm YES`；可用 `--dry-run` 预览。
