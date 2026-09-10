#!/usr/bin/env python3
"""POST /document-database/admin/addOrgMember — 添加普通组织成员（role=0）

将部门加入整个空间会扩大该部门下人员权限面。
已是管理员组织不可用本脚本降权，请用 update-org-member-role.py。
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

API_PATH = "/document-database/admin/addOrgMember"


def main():
    p = DocdbArgumentParser(hint="""add-org-member.py 必须提供 project_id 与 --org-id。
真实写入还需 --confirm YES，且必须 --ack-space-expand YES。
示例: python3 -B <skill-dir>/scripts/admin/add-org-member.py 10001 --org-id 50005 --ack-space-expand YES --confirm YES
""")
    p.add_argument("project_id", type=int)
    p.add_argument("--org-id", type=int, required=True)
    p.add_argument(
        "--ack-space-expand",
        type=str,
        default="",
        help="必须为 YES：确认将组织加入整个空间",
    )
    add_safety_args(p)
    args = p.parse_args()
    if not getattr(args, "dry_run", False) and args.ack_space_expand != "YES":
        print(
            "错误: 加组织成员会扩大该部门对整个空间的权限面。"
            "若仍要添加，须同时传入 --ack-space-expand YES 与 --confirm YES",
            file=sys.stderr,
        )
        sys.exit(2)
    body = {"projectId": args.project_id, "orgId": args.org_id}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
