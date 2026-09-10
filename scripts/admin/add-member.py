#!/usr/bin/env python3
"""POST /document-database/admin/addMember — 添加空间普通成员（role=0）

高风险：将人员加入整个空间会扩大权限面。
非空间成员只需访问指定目录时，应优先走协同分享（默认查看列表+在线预览），不要加空间成员。
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

API_PATH = "/document-database/admin/addMember"


def main():
    p = DocdbArgumentParser(hint="""add-member.py 必须提供 project_id 与 --employee-id。
真实写入还需 --confirm YES，且必须 --ack-space-expand YES（确认权限面扩大到整个空间）。
非成员目录访问请优先: upsert-file-share-grants.py（默认查看列表+在线预览）。
示例: python3 -B <skill-dir>/scripts/admin/add-member.py 10001 --employee-id 1 --ack-space-expand YES --confirm YES
""")
    p.add_argument("project_id", type=int)
    p.add_argument("--employee-id", type=int, required=True)
    p.add_argument(
        "--ack-space-expand",
        type=str,
        default="",
        help="必须为 YES：确认将对方加入整个空间（权限面大于单目录分享）",
    )
    # 兼容旧参数名
    p.add_argument(
        "--ack-personal-space-expand",
        type=str,
        default="",
        help="同 --ack-space-expand（兼容旧名）",
    )
    add_safety_args(p)
    args = p.parse_args()
    ack = args.ack_space_expand or args.ack_personal_space_expand
    if not getattr(args, "dry_run", False) and ack != "YES":
        print(
            "错误: 加空间成员会扩大对方对整个空间的权限面；"
            "目录级最小权限请用协同分享 upsert-file-share-grants.py。"
            "若仍要加成员，须同时传入 --ack-space-expand YES 与 --confirm YES",
            file=sys.stderr,
        )
        sys.exit(2)
    body = {"projectId": args.project_id, "employeeId": args.employee_id}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
