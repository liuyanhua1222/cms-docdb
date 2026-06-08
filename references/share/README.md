# share — 模块说明（授权分享）

## 适用场景

- 用户要把某个知识库文件/文件夹 **分享给某个人**（协同分享/授权）
- 用户要“给某人开权限”，并且希望 **默认发送钉钉分享通知**
- 用户未明确权限，要求默认给到：**分享 + 在线预览 + 查看**
- 用户在授权后还需要：**分享预览短链** 或 **查看分享记录**

## 鉴权模式

所有动作统一使用 `appKey` 鉴权，通过 `cms-auth-skills` 获取。

## 员工 ID（empId）获取方式（必须遵循用户服务文档）

分享对象必须是 **员工 ID（empId）**。

当用户只提供“姓名/关键词”而没有提供 empId 时：

1. 先调用 `scripts/share/search-emp-by-name.py`（对应用户服务 `GET /open-api/cwork-user/searchEmpByName`）
2. 从返回的 `data.inside.empList[].id` 取到 empId（可能有多条，需要让用户确认具体是哪一个）

> 参考文档：`dev-guide/02.产品业务AI文档/基础服务/API接口明细/01-用户服务.md` 的 **3.1 按姓名搜索全部员工**。

## 脚本清单

| 脚本 | 对应接口 | 用途 |
|---|---|---|
| `scripts/share/search-emp-by-name.py` | `GET /open-api/cwork-user/searchEmpByName` | 按姓名搜索员工并拿到 empId |
| `scripts/share/get-my-share-permissions.py` | `GET /open-api/document-database/share/getMySharePermissions` | 查询“调用方对指定 fileId 的可分享权限上限子集” |
| `scripts/share/upsert-file-share-grants.py` | `POST /open-api/document-database/share/upsertFileShareGrants` | **推荐**：授权分享（存在则更新、不存在则新增；不删他人；默认发钉钉通知；默认权限为分享+预览+查看） |
| `scripts/share/get-file-shares.py` | `GET /open-api/document-database/share/getFileShares` | 获取文件/文件夹的协同分享记录列表（人员/部门等） |
| `scripts/share/get-share-url.py` | `GET /open-api/document-database/share/getShareUrl` | 生成文件/文件夹的“可转发预览短链”（授权后用于链接分发） |
| `scripts/share/revoke-file-share-grants.py` | `POST /open-api/document-database/share/revokeFileShareGrants` | 撤销指定员工的协同分享（幂等；不发送钉钉通知） |
| `scripts/share/list-shared-to-me.py` | `GET /open-api/document-database/share/sharedToMe` | 分享给我的文件列表（分页；`fileName`/`sharerId` 筛选） |
| `scripts/share/list-my-shares.py` | `GET /open-api/document-database/share/myShares` | 我的分享列表（分页；`fileName` 筛选） |

## 输入要求

| 动作 | 必填输入 | 可选输入 |
|---|---|---|
| 搜索员工（拿 empId） | nameKey（姓名/关键词） | — |
| 查询可分享权限上限 | fileId | — |
| 授权分享（upsert） | fileId, empId | permissions, dueDate, name, isSendNotice, printShareUrl, source |
| 获取分享记录 | fileId | — |
| 获取分享短链 | fileId | source |
| 撤销分享 | fileId, empIds | — |

## 与前端「权限设置 / 分享权限管理」的对应关系（排错必读）

docdb 里有两套**不同的数据表与 UI**，不要混用：

| 产品入口 | 前端位置 | 读接口 | 写接口 | 数据表 |
|---|---|---|---|---|
| **分享权限管理** | 文件「邀请协作者」→「分享权限管理」 | `GET /share/getFileShares` | `POST /share/upsertFileShareGrants` 等 | `t_file_share` |
| **权限设置** | 知识库目录树右键「权限设置」 | `GET /fileGrant/getFileGrantByFileIdV2` | `POST /fileGrant/updateFileGrant`（未对 open-api 开放） | `t_file_grant` |

open-api / skill 的 **`upsertFileShareGrants` 只写 `t_file_share`**，与「分享权限管理」一致，**不会**写入 `t_file_grant`。

`getMySharePermissions` 虽走 `/fileGrant/getPermissionsByFileId`，但仅是分享前**读**权限上限，不是「权限设置」写入。

## 关键规则（强制）

1. **权限上限约束**：被分享人的 `permissions` **不能超过调用方对该 fileId 的有效权限**。不确定时先跑 `get-my-share-permissions.py`。
2. **自定义授权权限**：若用户明确说明要授予的权限，则 **按用户指定的 `permissions`** 发起分享；未说明时才走默认权限。
3. **默认权限**：用户未指定权限时，默认给 `fileshare`（分享）、`preview`（在线预览）、`read`（查看）。
4. **有效期默认永久**：默认需要传 `dueDate=20991231` 表示长期有效；如用户指定有效期，按用户提供的 `dueDate（yyyyMMdd）` 传入。
5. **默认通知**：默认 `isSendNotice=true`（发送钉钉分享通知）。除非用户明确要求不通知，才设置为 false。
6. **分享对象**：仅支持内部员工 empId（不支持 cpUserId / 其他第三方用户 ID）。
7. **重复授权**：使用 `upsert-file-share-grants.py`（对接 `upsertFileShareGrants`），对已授权对象会更新权限，不会出现“返回成功但未生效”。
8. **撤销分享**：使用 `revoke-file-share-grants.py`；无分享记录的员工进入 `notFoundEmpIds`（幂等）；**不发送**钉钉通知。

## 用户感知与对话输出规范（建议）

> 说明：本模块不实现“通过汇报发送”。默认送达方式为：`isSendNotice=true` 的钉钉分享通知；同时可生成短链供用户复制转发。

### A. 授权分享前确认（推荐）

当用户说“把这份文件分享给某人/给某人开权限”时，先用一句话确认关键信息：

```text
你要把《{fileName}》分享给 {targetName}。

默认权限：分享 + 在线预览 + 查看
有效期：长期有效（20991231）
通知方式：发送钉钉分享通知

是否确认分享？
```

若用户明确指定权限/有效期/不通知，则按用户输入覆盖默认值。

### B. 分享完成后的反馈（推荐）

分享成功后建议输出（面向用户的“结果卡片”文本）。必须先调用 `get-share-url.py` 拿到 `{shareUrl}`，并在卡片中**只回显原始 URL 字符串**（不要使用 Markdown 超链如 `[打开链接](url)`，混排时易被错误解析为链接，反而无法打开）：

```text
已完成分享 ✅

文件：{fileName}
分享给：{targetName}
权限：{grantedPermissions}
有效期：长期有效
分享链接：{shareUrl}

仅已授权成员可直接访问；未授权成员打开链接后，可在页面上申请权限。

下一步：
- 查看分享记录：可让我查询当前分享列表
```

### C. 生成短链与分享记录的建议编排

- 生成短链：分享成功后立即调用 `get-share-url.py` 获取 `{shareUrl}`，在分享反馈中原样输出 URL（纯文本，不做超链）
- 分享记录：分享成功后可继续调用 `get-file-shares.py` 回显“分享给谁/权限/有效期”

## 权限枚举（permissions）常用值

> 说明：最终可授予集合仍以 `get-my-share-permissions.py` 返回为准（必须是调用方对该文件的有效权限子集）。

- `read`：查看（列表/元数据）
- `preview`：在线预览
- `download`：下载
- `upload`：上传/更新
- `delete`：删除
- `fileshare`：分享
- `permmanage`：权限管理
- `admin`：管理员

## 权限包（面向用户的权限选项，建议）

> 说明：底层权限较细，面向普通用户建议只暴露“权限包”。本模块的默认权限包为：**分享 + 在线预览 + 查看**。

- **仅查看** = `read + preview + fileshare`
- **可下载** = `read + preview + download + fileshare`
- **可编辑** = `read + preview + download + upload + fileshare`
- **管理员** = `admin`（表示全权限）

默认权限包（按我们已确认的需求）：

- **默认权限**：`fileshare + preview + read`（分享 + 在线预览 + 查看）
- 如用户要求“仅查看/可下载/可编辑/管理员”，则按上述映射转换为 `permissions`

## 运行方式速查

```bash
# 1) 通过姓名搜索员工，拿到 empId
python3 scripts/share/search-emp-by-name.py "张三"

# 2)（可选）查询调用方对 fileId 的可分享权限上限（用于防止超额授权）
python3 scripts/share/get-my-share-permissions.py 2029019008342265857

# 3) 分享给某员工（upsert；默认权限：fileshare,preview,read；默认发送钉钉通知）
python3 scripts/share/upsert-file-share-grants.py 2029019008342265857 --emp-id 10001

# 3.1) 分享成功后一并输出短链
python3 scripts/share/upsert-file-share-grants.py 2029019008342265857 --emp-id 10001 --print-share-url --source "open_api"

# 4) 显式指定权限（逗号分隔）
python3 scripts/share/upsert-file-share-grants.py 2029019008342265857 --emp-id 10001 --permissions "read,preview,download"

# 4.1) 显式指定到期日（yyyyMMdd）；不传时默认会按长期有效处理（dueDate=20991231）
python3 scripts/share/upsert-file-share-grants.py 2029019008342265857 --emp-id 10001 --permissions "read,preview" --due-date 20991231

# 5) 不发送钉钉通知（用户明确要求时才用）
python3 scripts/share/upsert-file-share-grants.py 2029019008342265857 --emp-id 10001 --no-notice

# 6) 授权后生成可转发的预览短链接（用于分发给他人打开）
python3 scripts/share/get-share-url.py 2029019008342265857 --source "external"

# 7) 查看该文件/文件夹当前协同分享列表（谁被授权了哪些权限、有效期等）
python3 scripts/share/get-file-shares.py 2029019008342265857

# 8) 撤销指定员工的分享（empId 逗号分隔）
python3 scripts/share/revoke-file-share-grants.py 2029019008342265857 --emp-ids 10002,10003
```

