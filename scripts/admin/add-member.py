#!/usr/bin/env python3
"""POST /document-database/admin/addMember — 添加空间普通成员（role=0）"""
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
    p = DocdbArgumentParser(hint="""add-member.py 必须提供 project_id 与 --employee-id；真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/admin/add-member.py 10001 --employee-id 1 --confirm YES；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("project_id", type=int)
    p.add_argument("--employee-id", type=int, required=True)
    add_safety_args(p)
    args = p.parse_args()
    body = {"projectId": args.project_id, "employeeId": args.employee_id}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
