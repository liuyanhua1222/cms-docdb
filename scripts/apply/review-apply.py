#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/review — 审批权限申请（pass/refuse）"""
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

API_PATH = "/document-database/fileGrant/apply/review"


def main():
    p = DocdbArgumentParser(hint="""review-apply.py 必须提供 apply_id 与 --action；真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/apply/review-apply.py 12345 --action "pass" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("apply_id", type=int)
    p.add_argument("--action", required=True, choices=["pass", "refuse"])
    p.add_argument("--permissions", default=None, help="pass 时：逗号分隔")
    p.add_argument("--due-date", type=int, default=20991231)
    p.add_argument("--reason", default=None, help="refuse 时必填")
    add_safety_args(p)
    args = p.parse_args()
    body = {"applyId": args.apply_id, "action": args.action}
    if args.action == "pass":
        if not args.permissions:
            print("错误: pass 须指定 --permissions", file=sys.stderr); sys.exit(1)
        body["permissions"] = [x.strip() for x in args.permissions.split(",") if x.strip()]
        body["dueDate"] = args.due_date
    else:
        if not args.reason:
            print("错误: refuse 须指定 --reason", file=sys.stderr); sys.exit(1)
        body["reason"] = args.reason
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
