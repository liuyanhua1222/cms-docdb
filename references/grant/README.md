# grant — 目录授权（t_file_grant）

与 `share` 模块（`t_file_share` 协同分享）不同。被授权人**须为空间成员**；非成员须先 `add-member` 或走协同分享。

**增量语义**：仅影响请求中的用户，不删除他人授权。禁止全量 replace。

运行时由小龙虾上下文注入 `appkey`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

## 脚本清单

| 脚本 | 接口 |
|------|------|
| `scripts/grant/upsert-file-grants.py` | `POST .../fileGrant/upsertGrants` |
| `scripts/grant/revoke-file-grants.py` | `POST .../fileGrant/revokeGrants` |
| `scripts/admin/is-project-member.py` | `GET .../admin/isProjectMember`（授权前自检） |

不可授予 `admin`、`permmanage`。

## 示例

```bash
python3 scripts/admin/is-project-member.py 888
python3 scripts/grant/upsert-file-grants.py 123456 --emp-id 10002 --permissions "read,preview,download"
python3 scripts/grant/revoke-file-grants.py 123456 --emp-ids 10002
```
