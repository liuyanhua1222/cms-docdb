# apply — 权限申请与审批

> **调用方式（强制）**：使用 `openapi_skill_exec`，`skillCode`=`cms-docdb`，`toolName` 为下表/示例中的工具名；`argv` 只含业务参数。禁止标准 `exec`、脚本路径与 appKey。


## 流程（提交申请）

1. `get-approvers.py <file_id>` — 获取可选审批人（支持 `--keyword`）
2. **用户选择** `approverIds`（禁止默认全员）
3. `submit-apply.py` — 提交申请

## 脚本清单

| 脚本 | 接口 | 用途 |
|------|------|------|
| `scripts/apply/get-approvers.py` | `GET .../fileGrant/apply/approvers` | 查询可申请的管理员 |
| `scripts/apply/submit-apply.py` | `POST .../fileGrant/apply/submit` | 提交权限申请 |
| `scripts/apply/list-my-applies.py` | `POST .../fileGrant/apply/myApplies` | 我的申请列表（支持 `--keyword`） |
| `scripts/apply/list-pending-applies.py` | `POST .../fileGrant/apply/pending` | 待我处理（支持 `--keyword`） |
| `scripts/apply/list-processed-applies.py` | `POST .../fileGrant/apply/processed` | 我已处理（支持 `--keyword`） |
| `scripts/apply/review-apply.py` | `POST .../fileGrant/apply/review` | 审批（pass/refuse） |
| `scripts/admin/add-member.py` | `POST .../admin/addMember` | 添加空间普通成员 |
| `scripts/admin/is-project-member.py` | `GET .../admin/isProjectMember` | 判断是否空间成员 |

申请列表分页 `pageIndex` 从 **1** 开始。

### 列表查询参数

三个列表接口（我的申请/待我处理/我已处理）支持以下可选参数：

- `--keyword` - 统一关键字，模糊匹配申请人姓名/文件名/申请事由
- `--proposer` - 申请人姓名
- `--department` - 申请人部门
- `--status` - 状态筛选（1-申请中，2-通过，3-拒绝）
- `--page-index` - 页码（从 1 开始）
- `--page-size` - 每页数量


## 禁止调用的接口

- 全量 replace：`updateFileShare`、`updateFileGrantV2`
- 内部 `apply/info`（权限由 submit 入参显式传入）

## 列表接口响应字段说明（FileGrantApplyVO）

`list-my-applies.py`、`list-pending-applies.py`、`list-processed-applies.py` 及 `review-apply.py` 详情的 `pageData` 元素字段：

| 字段 | 说明 |
|---|---|
| `id` | 申请 id |
| `fileId` | 文件 id |
| `fileName` | 文件名 |
| `fileType` | 文件类型：`doc`/`file`/`work_report`/`work_plan` |
| `suffix` | 文件后缀 |
| `type` | 资源类型：`1` 文件夹，`2` 文件，`3` 库 |
| `filePath` | 文件路径 |
| `projectId` | 空间 id |
| `projectName` | 空间名称 |
| `applyType` | `add` / `update` |
| `sourceType` | `1`-permissions，`2`-share |
| `status` | `1` 申请中，`2` 通过，`3` 拒绝 |
| `applyPermissions` | 申请的权限列表 |
| `oldPermissions` | 申请前已有权限 |
| `auditPermissions` | 审核后授予权限 |
| `applyRemark` | 申请原因 |
| `auditRemark` | 审核备注 |
| `applyDueDate` | 申请有效期 yyyyMMdd |
| `auditDueDate` | 审核后有效期 |
| `applyTime` | 申请日期 yyyy-MM-dd |
| `applyEmp` | 申请人信息（含 `id`/`name`/`avatar`） |
| `auditEmp` | 审核人信息（含 `id`/`name`/`avatar`） |
| `auditEmpList` | 审核人列表（多审批人） |
| `isProjectMember` | 申请人是否空间成员 |
| `isAllHave` | 申请权限是否已全部拥有 |
| `createTime` | 创建时间（毫秒时间戳） |

分页响应新增 `pageCount`（总页数）字段。

## 示例

**调用方式（强制）**：使用 `openapi_skill_exec`，`skillCode`=`cms-docdb`；`argv` 只含业务参数。禁止标准 `exec`、脚本路径与 appKey。


```bash
`openapi_skill_exec` `toolName`=`get-approvers`，argv: 123456 --keyword "张"
`openapi_skill_exec` `toolName`=`submit-apply`，argv: 123456 --permissions "read,preview" --reason "查阅方案" --approver-ids 1001 --confirm YES
`openapi_skill_exec` `toolName`=`list-my-applies`，argv: --page-index 1 --page-size 20
`openapi_skill_exec` `toolName`=`list-my-applies`，argv: --keyword "技术方案" --page-index 1 --page-size 20
`openapi_skill_exec` `toolName`=`list-pending-applies`，argv: --page-index 1 --page-size 20
`openapi_skill_exec` `toolName`=`list-pending-applies`，argv: --keyword "张三" --status 1
`openapi_skill_exec` `toolName`=`review-apply`，argv: 99 --action pass --permissions "read,preview" --confirm YES
`openapi_skill_exec` `toolName`=`review-apply`，argv: 99 --action refuse --reason "理由不充分" --confirm YES
`openapi_skill_exec` `toolName`=`add-member`，argv: 888 --employee-id 10002 --confirm YES
```
