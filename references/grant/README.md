# grant — 目录授权（t_file_grant）

> **调用方式（强制）**：标准 `exec` + python3 -B <skill-dir>/scripts/...；将 `<skill-dir>` 换成本 skill 根目录绝对路径；命令含业务参数 + 可选 `--app-key`。


与 `share` 模块（`t_file_share` 协同分享）不同。被授权人**须为空间成员**；非成员优先走协同分享（默认查看列表+在线预览）。**个人知识库禁止 `add-member`**，勿扩大个人库空间权限面。

**增量语义**：仅影响请求中的用户，不删除他人授权。禁止全量 replace。

权限 UI 用语与 `share` 相同：查看列表 / 在线预览 / 下载 / 删除 / 上传/编辑 / 分享 / 权限管理 / 管理员。脚本拒绝授予 `admin`、`permmanage`。

## 权限策略

| 阶段 | 规则 |
|---|---|
| 新授权 | 必须指定 permissions（建议最小只读 `read,preview`）；白名单校验 |
| 编辑减权 | `read`（查看列表）兜底；保留原 dueDate；`preview`/`download` 等可单独去掉 → `strip-grant-permissions.py` |
| 整单收回 | `revoke-file-grants.py`（勿用于单项减权） |


## 脚本清单

| 脚本 | 接口 |
|------|------|
| `scripts/grant/upsert-file-grants.py` | `POST .../fileGrant/upsertGrants` |
| `scripts/grant/get-file-grants.py` | `GET .../fileGrant/getGrants` |
| `scripts/grant/strip-grant-permissions.py` | 单项减权（内部 upsert） |
| `scripts/grant/revoke-file-grants.py` | `POST .../fileGrant/revokeGrants`（整单收回） |
| `scripts/grant/get-inherit-permission.py` | `GET .../fileGrant/getInheritPermission` |
| `scripts/grant/preview-inherit-change.py` | `GET .../fileGrant/previewInheritChange` |
| `scripts/grant/update-inherit-permission.py` | `POST .../fileGrant/updateInheritPermission` |
| `scripts/admin/is-project-member.py` | `GET .../admin/isProjectMember`（授权前自检） |

不可授予 `admin`、`permmanage`（关闭继承时的 `promoteCallerAsAdmin` 为例外，仅把调用方落为本级 admin）。

## 权限继承（文件夹）

保密子目录闭环：`get-inherit-permission` → `preview-inherit-change` → `update-inherit-permission`（可 `--promote-caller-as-admin`）→ `upsert`/`revoke` 配本级权。

```bash
python3 -B <skill-dir>/scripts/grant/get-inherit-permission.py 123456
python3 -B <skill-dir>/scripts/grant/preview-inherit-change.py 123456 --cancel-inherit true
python3 -B <skill-dir>/scripts/grant/update-inherit-permission.py 123456 --cancel-inherit true --dry-run
python3 -B <skill-dir>/scripts/grant/update-inherit-permission.py 123456 --cancel-inherit true --server-dry-run --confirm YES
python3 -B <skill-dir>/scripts/grant/update-inherit-permission.py 123456 --cancel-inherit true --promote-caller-as-admin --confirm YES
```

## 示例

**调用方式（强制）**：标准 `exec` + python3 -B <skill-dir>/scripts/...；将 `<skill-dir>` 换成本 skill 根目录绝对路径；命令含业务参数 + 可选 `--app-key`。


```bash
python3 -B <skill-dir>/scripts/admin/is-project-member.py 888
python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 123456 --emp-id 10002 --permissions "read,preview,download" --dry-run
python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 123456 --emp-id 10002 --permissions "download" --confirm YES
python3 -B <skill-dir>/scripts/grant/get-file-grants.py 123456
python3 -B <skill-dir>/scripts/grant/strip-grant-permissions.py 123456 --emp-id 10002 --remove download --confirm YES
python3 -B <skill-dir>/scripts/grant/revoke-file-grants.py 123456 --emp-ids 10002 --confirm YES
```

写入类须先获用户确认，再带 `--confirm YES`；可用 `--dry-run` 预览。
