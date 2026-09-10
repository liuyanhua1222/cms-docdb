#!/usr/bin/env python3
"""POST /document-database/admin/removeOrgMember — 移除普通组织成员（role=0）

仅可移除普通组织；管理员组织须先 update-org-member-role 降为 0。
目标已不在成员中时接口幂等成功。
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

API_PATH = "/document-database/admin/removeOrgMember"


def main():
    p = DocdbArgumentParser(hint="""remove-org-member.py 必须提供 project_id 与 --org-id。
真实写入还需 --confirm YES，且必须 --ack-space-shrink YES。
示例: python3 -B <skill-dir>/scripts/admin/remove-org-member.py 10001 --org-id 50005 --ack-space-shrink YES --confirm YES
""")
    p.add_argument("project_id", type=int)
    p.add_argument("--org-id", type=int, required=True)
    p.add_argument(
        "--ack-space-shrink",
        type=str,
        default="",
        help="必须为 YES：确认将组织移出整个空间",
    )
    add_safety_args(p)
    args = p.parse_args()
    if not getattr(args, "dry_run", False) and args.ack_space_shrink != "YES":
        print(
            "错误: 移除组织成员会收回该部门对整个空间的权限面。"
            "若仍要移除，须同时传入 --ack-space-shrink YES 与 --confirm YES",
            file=sys.stderr,
        )
        sys.exit(2)
    body = {"projectId": args.project_id, "orgId": args.org_id}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
