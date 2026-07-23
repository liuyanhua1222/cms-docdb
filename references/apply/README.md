# apply — 权限申请与审批

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

运行时由小龙虾上下文注入 `appkey`。文档与示例统一写 `python3`；执行时优先 `python3`，若不可用（常见于部分 Windows 仅有 `python` 命令）则改用 `python` 等价替换。

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

**重要说明**：以下示例使用相对路径以便阅读，实际执行时必须替换为绝对路径。例如：
- 文档示例：`python3 -B <skill-dir>/scripts/apply/get-approvers.py 123456`
- 实际执行：`python3 -B <skill-dir>/scripts/apply/get-approvers.py 123456`（将 `<skill-dir>` 换成 skill 根目录绝对路径）

禁止使用 `cd`、`&&`、管道等 shell 构造。每个脚本必须在单独的命令中使用绝对路径执行。

```bash
python3 -B <skill-dir>/scripts/apply/get-approvers.py 123456 --keyword "张"
python3 -B <skill-dir>/scripts/apply/submit-apply.py 123456 --permissions "read,preview" --reason "查阅方案" --approver-ids 1001 --confirm YES
python3 -B <skill-dir>/scripts/apply/list-my-applies.py --page-index 1 --page-size 20
python3 -B <skill-dir>/scripts/apply/list-my-applies.py --keyword "技术方案" --page-index 1 --page-size 20
python3 -B <skill-dir>/scripts/apply/list-pending-applies.py --page-index 1 --page-size 20
python3 -B <skill-dir>/scripts/apply/list-pending-applies.py --keyword "张三" --status 1
python3 -B <skill-dir>/scripts/apply/review-apply.py 99 --action pass --permissions "read,preview" --confirm YES
python3 -B <skill-dir>/scripts/apply/review-apply.py 99 --action refuse --reason "理由不充分" --confirm YES
python3 -B <skill-dir>/scripts/admin/add-member.py 888 --employee-id 10002 --confirm YES
```
