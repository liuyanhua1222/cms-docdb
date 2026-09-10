#!/usr/bin/env python3
"""POST /document-database/fileGrant/updateInheritPermission — 关闭或恢复上级权限继承"""
import sys
import os
import json

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

API_PATH = "/document-database/fileGrant/updateInheritPermission"


def main():
    p = DocdbArgumentParser(
        hint="""update-inherit-permission.py 必须提供 --file-id、--cancel-inherit；真实写入还需 --confirm YES。
预检优先用 preview-inherit-change.py；本脚本 --dry-run 只打印拟发请求。
本级无管理员时可加 --promote-caller-as-admin；也可 --server-dry-run 走接口 dryRun=true。
示例: python3 -B <skill-dir>/scripts/grant/update-inherit-permission.py --file-id 12345 --cancel-inherit true --dry-run
示例: python3 -B <skill-dir>/scripts/grant/update-inherit-permission.py --file-id 12345 --cancel-inherit true --promote-caller-as-admin --confirm YES
"""
    )
    p.add_argument("--file-id", dest="file_id", required=True, type=int)
    p.add_argument(
        "--cancel-inherit",
        required=True,
        choices=["true", "false"],
        help="true=关闭上级继承；false=恢复",
    )
    p.add_argument(
        "--promote-caller-as-admin",
        action="store_true",
        help="关闭继承且本级无 admin 时，将调用方写为本级 admin",
    )
    p.add_argument(
        "--server-dry-run",
        action="store_true",
        help="请求体 dryRun=true（服务端预检不落库）；仍须 --confirm YES",
    )
    add_safety_args(p)
    args = p.parse_args()
    body = {
        "fileId": args.file_id,
        "cancelInherit": args.cancel_inherit == "true",
        "promoteCallerAsAdmin": bool(args.promote_caller_as_admin),
        "dryRun": bool(args.server_dry_run),
    }
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
