#!/usr/bin/env python3
"""POST /document-database/fileGrant/upsertGrants — 增量目录授权（t_file_grant）"""
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

API_PATH = "/document-database/fileGrant/upsertGrants"


def main():
    p = DocdbArgumentParser(hint="""upsert-file-grants.py 必须提供 file_id、--emp-id、--permissions；真实写入还需 --confirm YES。
权限名对齐 UI：查看列表/在线预览/下载/删除/上传/编辑/分享等；禁止 admin/permmanage。
示例: python3 -B <skill-dir>/scripts/grant/upsert-file-grants.py 12345 --emp-id 1 --permissions "read,preview" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("file_id", type=int)
    p.add_argument("--emp-id", type=int, required=True)
    p.add_argument("--permissions", required=True, help="逗号分隔，如 read,preview")
    p.add_argument("--due-date", type=int, default=20991231)
    add_safety_args(p)
    args = p.parse_args()
    try:
        perms = validate_grant_permissions(parse_permission_csv(args.permissions))
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)
    body = {
        "fileId": args.file_id,
        "grants": [{
            "empId": args.emp_id,
            "permissions": perms,
            "dueDate": args.due_date,
        }],
    }
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    if isinstance(result, dict):
        result = dict(result)
        result["grantedLabels"] = labels_for(perms)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
