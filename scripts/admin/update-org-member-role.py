#!/usr/bin/env python3
"""POST /document-database/admin/updateOrgMemberRole — 更新组织成员角色（0/1）

降权后若空间无管理员会失败。
升权到 1 须 --ack-role-elevate YES。
个人知识库禁止升权（仅允许同角色或降为 0）。
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

API_PATH = "/document-database/admin/updateOrgMemberRole"
ALLOWED = {0, 1}


def main():
    p = DocdbArgumentParser(hint="""update-org-member-role.py 必须提供 --project-id、--org-id、--role。
role 仅 0/1。真实写入需 --confirm YES；升权到 1 另需 --ack-role-elevate YES。
个人知识库禁止升权，仅允许降为普通(0)。
示例: python3 -B <skill-dir>/scripts/admin/update-org-member-role.py --project-id 10001 --org-id 50005 --role 0 --confirm YES
""")
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    p.add_argument("--org-id", type=int, required=True)
    p.add_argument("--role", type=int, required=True, choices=sorted(ALLOWED))
    p.add_argument(
        "--ack-role-elevate",
        type=str,
        default="",
        help="升权到组织管理员时必须为 YES",
    )
    add_safety_args(p)
    args = p.parse_args()
    if args.role == 1 and not getattr(args, "dry_run", False) and args.ack_role_elevate != "YES":
        print(
            "错误: 升权为组织管理员须同时传入 --ack-role-elevate YES 与 --confirm YES",
            file=sys.stderr,
        )
        sys.exit(2)
    body = {"projectId": args.project_id, "orgId": args.org_id, "role": args.role}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
