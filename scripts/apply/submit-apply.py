#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/submit — 提交权限申请（须先 get-approvers 选择审批人）"""
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

API_PATH = "/document-database/fileGrant/apply/submit"


def main():
    p = DocdbArgumentParser(hint="""submit-apply.py 必须提供 file_id、--permissions、--reason、--approver-ids；真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/apply/submit-apply.py 12345 --permissions "read,preview" --reason "需要查阅" --approver-ids 1 --confirm YES；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("file_id", type=int)
    p.add_argument("--permissions", required=True, help="逗号分隔，如 read,preview,download")
    p.add_argument("--reason", required=True)
    p.add_argument("--approver-ids", required=True, help="逗号分隔的 employeeId")
    p.add_argument("--due-date", type=int, default=20991231)
    add_safety_args(p)
    args = p.parse_args()
    body = {
        "fileId": args.file_id,
        "permissions": [x.strip() for x in args.permissions.split(",") if x.strip()],
        "reason": args.reason,
        "approverIds": [int(x.strip()) for x in args.approver_ids.split(",") if x.strip()],
        "dueDate": args.due_date,
    }
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
