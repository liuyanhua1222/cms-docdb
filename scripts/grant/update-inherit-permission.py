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
升权调试：须同时 --promote-caller-as-admin、--confirm PROMOTE、CMS_DOCDB_NONPROD=1（生产不可用）。
示例: python3 -B <skill-dir>/scripts/grant/update-inherit-permission.py --file-id 12345 --cancel-inherit true --dry-run
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
        help="高危：关闭继承且本级无 admin 时将调用方写为本级 admin（须非生产+--confirm PROMOTE）",
    )
    p.add_argument(
        "--server-dry-run",
        action="store_true",
        help="请求体 dryRun=true（服务端预检不落库）；仍须 --confirm YES",
    )
    add_safety_args(p)
    args = p.parse_args()

    promote = bool(args.promote_caller_as_admin)
    if promote:
        if os.environ.get("CMS_DOCDB_NONPROD") != "1":
            print(
                "错误: --promote-caller-as-admin 仅允许非生产（须 CMS_DOCDB_NONPROD=1）；"
                "生产请走正式管理员授权流程",
                file=sys.stderr,
            )
            sys.exit(2)
        if not args.dry_run and args.confirm != "PROMOTE":
            print(
                "错误: 升权调试须 --confirm PROMOTE（不可用 YES）",
                file=sys.stderr,
            )
            sys.exit(2)

    body = {
        "fileId": args.file_id,
        "cancelInherit": args.cancel_inherit == "true",
        "promoteCallerAsAdmin": promote,
        "dryRun": bool(args.server_dry_run),
    }
    # promote 场景 confirm 已是 PROMOTE；safety 层对非 YES 会拦，故 promote 时绕过 enforce 的 confirm 检查
    if promote and not args.dry_run:
        # 直接调用，已做过双重门禁
        result = request_open_api(API_PATH, method="POST", body=body)
        print(json.dumps(result, ensure_ascii=False))
        return

    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
