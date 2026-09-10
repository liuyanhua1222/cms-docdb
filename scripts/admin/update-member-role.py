#!/usr/bin/env python3
"""POST /document-database/admin/updateMemberRole — 更新员工成员角色（0/1/3）

禁止改助理(2)。降权后若空间无管理员会失败。
升权到 1 或 3 须 --ack-role-elevate YES。
个人知识库禁止升权（仅允许同角色或降为 0 以便清历史后再 remove）。
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
from docdb_open_api import ensure_common_on_path, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

API_PATH = "/document-database/admin/updateMemberRole"
ALLOWED = {0, 1, 3}


def main():
    p = DocdbArgumentParser(hint="""update-member-role.py 必须提供 --project-id、--employee-id、--role。
role 仅 0/1/3。真实写入需 --confirm YES；升权到 1 或 3 另需 --ack-role-elevate YES。
个人知识库禁止升权，仅允许降为普通成员(0)以便 remove。
示例: python3 -B <skill-dir>/scripts/admin/update-member-role.py --project-id 10001 --employee-id 1 --role 0 --confirm YES
""")
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    p.add_argument("--employee-id", type=int, required=True)
    p.add_argument("--role", type=int, required=True, choices=sorted(ALLOWED))
    p.add_argument(
        "--ack-role-elevate",
        type=str,
        default="",
        help="升权到管理员/安全管理员时必须为 YES",
    )
    add_safety_args(p)
    args = p.parse_args()
    if args.role in (1, 3) and not getattr(args, "dry_run", False) and args.ack_role_elevate != "YES":
        print(
            "错误: 升权为空间管理员/安全管理员须同时传入 --ack-role-elevate YES 与 --confirm YES",
            file=sys.stderr,
        )
        sys.exit(2)
    body = {"projectId": args.project_id, "employeeId": args.employee_id, "role": args.role}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
