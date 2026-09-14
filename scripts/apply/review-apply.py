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
from permissions import labels_for, parse_permission_csv, validate_grant_permissions

API_PATH = "/document-database/fileGrant/apply/review"


def main():
    p = DocdbArgumentParser(hint="""review-apply.py 必须提供 --apply-id 与 --action；真实写入还需 --confirm YES。
pass 时 --permissions 走公共白名单（与目录授权一致）。
示例: python3 -B <skill-dir>/scripts/apply/review-apply.py --apply-id 12345 --action "pass" --permissions "read,preview" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("--apply-id", dest="apply_id", required=True, type=int)
    p.add_argument("--action", required=True, choices=["pass", "refuse"])
    p.add_argument("--permissions", default=None, help="pass 时：逗号分隔")
    p.add_argument("--due-date", type=int, default=20991231, help="到期日；默认永久（产品确认）")
    p.add_argument("--reason", default=None, help="refuse 时必填")
    add_safety_args(p)
    args = p.parse_args()
    body = {"applyId": args.apply_id, "action": args.action}
    perms = None
    if args.action == "pass":
        if not args.permissions:
            print("错误: pass 须指定 --permissions", file=sys.stderr); sys.exit(1)
        try:
            perms = validate_grant_permissions(parse_permission_csv(args.permissions))
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(2)
        body["permissions"] = perms
        body["dueDate"] = args.due_date
    else:
        if not args.reason:
            print("错误: refuse 须指定 --reason", file=sys.stderr); sys.exit(1)
        body["reason"] = args.reason
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    if isinstance(result, dict) and perms is not None:
        result = dict(result)
        result["grantedLabels"] = labels_for(perms)
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
