#!/usr/bin/env python3
"""
share / upsertFileShareGrants 脚本

用途：将知识库文件/文件夹授权分享给指定员工 empId（存在则更新，不存在则新增，不删除他人授权）

默认行为（当用户未说明时）：
  - permissions 默认：read（查看列表）+ preview（在线预览）；不含 fileshare（分享）
  - dueDate 默认：20991231（长期有效；产品确认前保留）
  - isSendNotice 默认：true（默认发送钉钉分享通知）

使用方式：
  python3 -B <skill-dir>/scripts/share/upsert-file-share-grants.py --file-id 12345 --emp-id 1 --confirm YES

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
from permissions import (
    DEFAULT_SHARE_PERMISSIONS,
    ensure_subset_of_ceiling,
    labels_for,
    parse_permission_csv,
    validate_share_permissions,
)

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

BASE = "/document-database/share"
URL_UPSERT = f"{BASE}/upsertFileShareGrants"
URL_GET_SHARE_URL = f"{BASE}/getShareUrl"
URL_MY_PERMS = f"{BASE}/getMySharePermissions"

DEFAULT_PERMISSIONS = list(DEFAULT_SHARE_PERMISSIONS)
DEFAULT_DUE_DATE = 20991231


def call_json(method: str, url: str, body: dict = None, params: list = None) -> dict:
    return request_open_api(url, method=method, body=body, params=params)


def fetch_ceiling(file_id: int):
    """返回可分享权限 list；失败抛 ValueError（fail-closed）。"""
    try:
        resp = call_json("GET", URL_MY_PERMS, params=[("fileId", str(file_id))])
    except SystemExit:
        raise
    except Exception as e:
        raise ValueError(f"查询可分享权限上限失败: {e}") from e
    if not isinstance(resp, dict):
        raise ValueError("查询可分享权限上限失败: 响应非 JSON 对象")
    data = resp.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("permissions", "sharePermissions", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    code = resp.get("resultCode")
    msg = resp.get("resultMsg") or "无 data 权限列表"
    raise ValueError(f"查询可分享权限上限失败: resultCode={code}, {msg}")


def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result


def main():
    parser = DocdbArgumentParser(
        description="增量授予协同分享",
        hint="""upsert-file-share-grants.py 必须提供 --file-id，且必须带 --emp-id。
真实写入还需 --confirm YES。
默认权限：查看列表+在线预览（read,preview），不含分享。
示例: python3 -B <skill-dir>/scripts/share/upsert-file-share-grants.py --file-id 12345 --emp-id 1 --confirm YES；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("--file-id", dest="file_id", required=True, type=int, help="文件/文件夹 ID（fileId）")
    parser.add_argument("--emp-id", type=int, required=True, help="被分享员工 empId")
    parser.add_argument(
        "--permissions",
        type=str,
        help="权限逗号分隔；默认 read,preview（查看列表+在线预览）。显式需要分享时再加 fileshare",
    )
    parser.add_argument("--due-date", type=int, help="到期日期（yyyyMMdd）；不传默认 20991231（长期有效）")
    parser.add_argument("--name", type=str, help="被分享人姓名（可选，用于展示/通知）")
    parser.add_argument("--no-notice", action="store_true", help="不发送钉钉分享通知（默认发送）")
    parser.add_argument("--source", type=str, help="生成短链的 source（可选，配合 --print-share-url）")
    parser.add_argument("--print-share-url", action="store_true", help="成功后额外输出 shareUrl")
    parser.add_argument(
        "--skip-ceiling-check",
        action="store_true",
        help="跳过 getMySharePermissions 上限校验（不推荐；仅排障）",
    )
    add_safety_args(parser)
    args = parser.parse_args()

    try:
        raw = parse_permission_csv(args.permissions) if args.permissions else list(DEFAULT_PERMISSIONS)
        perms = validate_share_permissions(raw)
        # dry-run 不发 HTTP：跳过上限查询；真实写入默认 fail-closed
        if not args.skip_ceiling_check and not getattr(args, "dry_run", False):
            ceiling = fetch_ceiling(args.file_id)
            ensure_subset_of_ceiling(perms, ceiling)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)

    due_date = args.due_date if args.due_date is not None else DEFAULT_DUE_DATE
    is_send_notice = False if args.no_notice else True

    grant = {
        "empId": args.emp_id,
        "permissions": perms,
        "dueDate": due_date,
    }
    if args.name:
        grant["name"] = args.name

    body = {
        "fileId": args.file_id,
        "isSendNotice": is_send_notice,
        "shareGrants": [grant],
    }

    enforce_or_dry_run(args, method="POST", url=URL_UPSERT, body=body)
    result = call_json("POST", URL_UPSERT, body=body)
    processed = process_result(result)
    if isinstance(processed, dict):
        processed["grantedLabels"] = labels_for(perms)
        processed["grantedPermissions"] = perms

    if args.print_share_url:
        params = [("fileId", str(args.file_id))]
        if args.source:
            params.append(("source", args.source))
        url_resp = call_json("GET", URL_GET_SHARE_URL, params=params)
        out = {"result": processed, "shareUrl": url_resp.get("data") if isinstance(url_resp, dict) else None}
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(json.dumps(processed, ensure_ascii=False))


if __name__ == "__main__":
    main()
