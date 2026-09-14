#!/usr/bin/env python3
"""POST /document-database/fileGrant/upsertGrants — 增量目录授权（t_file_grant）

默认在写入前预检被授权人是否空间成员（isProjectMember）；可用 --skip-member-check 逃生。
查他人时不采信裸 Boolean（防旧网关忽略 employeeId）；不可信则 listMembers 回退。
"""
import sys, os, json

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, get_file_basic_info, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run
from permissions import labels_for, parse_permission_csv, validate_grant_permissions
from project_member_check import ensure_project_member

API_PATH = "/document-database/fileGrant/upsertGrants"


def main():
    p = DocdbArgumentParser(hint="""upsert-file-grants.py 必须提供 --file-id、--emp-id、--permissions；真实写入还需 --confirm YES。
权限名对齐 UI：查看列表/在线预览/下载/删除/上传/编辑/分享等；禁止 admin/permmanage。
默认预检被授权人是否空间成员；--skip-member-check 可跳过。
示例: python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py --file-id 12345 --emp-id 1 --permissions "read,preview" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("--file-id", dest="file_id", required=True, type=int)
    p.add_argument("--emp-id", type=int, required=True)
    p.add_argument("--permissions", required=True, help="逗号分隔，如 read,preview")
    p.add_argument("--due-date", type=int, default=20991231)
    p.add_argument(
        "--skip-member-check",
        action="store_true",
        help="跳过被授权人空间成员预检（不推荐；仅排障）",
    )
    p.add_argument(
        "--project-id",
        dest="project_id",
        type=int,
        default=None,
        help="可选；不传则从 fileId 反查 projectId 再预检",
    )
    add_safety_args(p)
    args = p.parse_args()
    try:
        perms = validate_grant_permissions(parse_permission_csv(args.permissions))
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)
    body = {
        "fileId": args.file_id,
        "grants": [{
            "empId": args.emp_id,
            "permissions": perms,
            "dueDate": args.due_date,
        }],
    }
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)

    if not args.skip_member_check:
        project_id = args.project_id
        if project_id is None:
            info = get_file_basic_info(args.file_id)
            project_id = info.get("projectId") if isinstance(info, dict) else None
        if project_id is None:
            print("错误: 无法解析 projectId，无法预检成员；可传 --project-id 或 --skip-member-check", file=sys.stderr)
            sys.exit(2)
        ensure_project_member(int(project_id), int(args.emp_id))

    result = request_open_api(API_PATH, method="POST", body=body)
    if isinstance(result, dict):
        result = dict(result)
        result["grantedLabels"] = labels_for(perms)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
