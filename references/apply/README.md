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
| `scripts/apply/list-my-applies.py` | `POST .../fileGrant/apply/myApplies` | 我的申请列表 |
| `scripts/apply/list-pending-applies.py` | `POST .../fileGrant/apply/pending` | 待我处理 |
| `scripts/apply/list-processed-applies.py` | `POST .../fileGrant/apply/processed` | 我已处理 |
| `scripts/apply/review-apply.py` | `POST .../fileGrant/apply/review` | 审批（pass/refuse） |
| `scripts/admin/add-member.py` | `POST .../admin/addMember` | 添加空间普通成员 |
| `scripts/admin/is-project-member.py` | `GET .../admin/isProjectMember` | 判断是否空间成员 |

申请列表分页 `pageIndex` 从 **1** 开始。

## 禁止调用的接口

- 全量 replace：`updateFileShare`、`updateFileGrantV2`
- 内部 `apply/info`（权限由 submit 入参显式传入）

## 示例

```bash
python3 scripts/apply/get-approvers.py 123456 --keyword "张"
python3 scripts/apply/submit-apply.py 123456 --permissions "read,preview" --reason "查阅方案" --approver-ids 1001
python3 scripts/apply/list-pending-applies.py --page-index 1 --page-size 20
python3 scripts/apply/review-apply.py 99 --action pass --permissions "read,preview"
python3 scripts/apply/review-apply.py 99 --action refuse --reason "理由不充分"
python3 scripts/admin/add-member.py 888 --employee-id 10002
```
