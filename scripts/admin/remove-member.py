#!/usr/bin/env python3
"""POST /document-database/admin/removeMember — 移除空间普通成员（role=0）

仅可移除普通成员；管理员/助理/安全员须走管理后台。
目标已不在成员中时接口幂等成功。
勿与目录授权 revoke、协同分享 revoke 混淆。
"""
import sys
import os
import json

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

API_PATH = "/document-database/admin/removeMember"


def main():
    p = DocdbArgumentParser(hint="""remove-member.py 必须提供 --project-id 与 --employee-id。
真实写入还需 --confirm YES，且必须 --ack-space-shrink YES（确认缩小对方整空间权限面）。
仅普通成员；目录级减权请用 strip/revoke 分享或目录授权脚本。
示例: python3 -B <skill-dir>/scripts/admin/remove-member.py --project-id 10001 --employee-id 1 --ack-space-shrink YES --confirm YES
""")
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    p.add_argument("--employee-id", type=int, required=True)
    p.add_argument(
        "--ack-space-shrink",
        type=str,
        default="",
        help="必须为 YES：确认将对方移出整个空间",
    )
    add_safety_args(p)
    args = p.parse_args()
    if not getattr(args, "dry_run", False) and args.ack_space_shrink != "YES":
        print(
            "错误: 移除空间成员会收回对方对整个空间的权限面；"
            "若仅去掉目录分享请用 revoke/strip 分享脚本。"
            "若仍要移出成员，须同时传入 --ack-space-shrink YES 与 --confirm YES",
            file=sys.stderr,
        )
        sys.exit(2)
    body = {"projectId": args.project_id, "employeeId": args.employee_id}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
