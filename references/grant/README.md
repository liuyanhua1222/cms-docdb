# grant — 目录授权（t_file_grant）

> **调用方式（强制）**：使用 `openapi_skill_exec`，`skillCode`=`cms-docdb`，`toolName` 为下表/示例中的工具名；`argv` 只含业务参数。禁止标准 `exec`、脚本路径与 appKey。


与 `share` 模块（`t_file_share` 协同分享）不同。被授权人**须为空间成员**；非成员须先 `add-member` 或走协同分享。

**增量语义**：仅影响请求中的用户，不删除他人授权。禁止全量 replace。

## 权限策略

| 阶段 | 规则 |
|---|---|
| 新授权 | 必须指定 permissions；服务端合并 `read+preview` + 指定项（不含 `fileshare`） |
| 编辑减权 | `read` 兜底；`preview`/`download` 等可单独去掉 → `strip-grant-permissions.py` |
| 整单收回 | `revoke-file-grants.py`（勿用于单项减权） |


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

**调用方式（强制）**：使用 `openapi_skill_exec`，`skillCode`=`cms-docdb`；`argv` 只含业务参数。禁止标准 `exec`、脚本路径与 appKey。


```bash
`openapi_skill_exec` `toolName`=`is-project-member`，argv: 888
`openapi_skill_exec` `toolName`=`upsert-file-grants`，argv: 123456 --emp-id 10002 --permissions "read,preview,download" --dry-run
`openapi_skill_exec` `toolName`=`upsert-file-grants`，argv: 123456 --emp-id 10002 --permissions "download" --confirm YES
`openapi_skill_exec` `toolName`=`get-file-grants`，argv: 123456
`openapi_skill_exec` `toolName`=`strip-grant-permissions`，argv: 123456 --emp-id 10002 --remove download --confirm YES
`openapi_skill_exec` `toolName`=`revoke-file-grants`，argv: 123456 --emp-ids 10002 --confirm YES
```

写入类须先获用户确认，再带 `--confirm YES`；可用 `--dry-run` 预览。
