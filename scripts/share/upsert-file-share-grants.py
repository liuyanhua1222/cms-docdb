#!/usr/bin/env python3
"""
share / upsertFileShareGrants 脚本

用途：将知识库文件/文件夹授权分享给指定员工 empId（存在则更新，不存在则新增，不删除他人授权）

默认行为（当用户未说明时）：
  - permissions 默认：fileshare（分享） + preview（在线预览） + read（查看）
  - dueDate 默认：20991231（长期有效）
  - isSendNotice 默认：true（默认发送钉钉分享通知）

使用方式：

"""

import sys
import urllib.parse
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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

BASE = "/document-database/share"
URL_UPSERT = f"{BASE}/upsertFileShareGrants"
URL_GET_SHARE_URL = f"{BASE}/getShareUrl"

DEFAULT_PERMISSIONS = ["fileshare", "preview", "read"]
DEFAULT_DUE_DATE = 20991231


def call_json(method: str, url: str, body: dict = None, params: list = None) -> dict:
    return request_open_api(url, method=method, body=body, params=params)

def parse_permissions(raw: str):
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",")]
    perms = [p for p in parts if p]
    return perms or None

def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result

def main():
    parser = DocdbArgumentParser(description="增量授予协同分享", hint="""upsert-file-share-grants.py 必须提供 file_id，且必须带 --emp-id。
真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/share/upsert-file-share-grants.py 12345 --emp-id 1 --confirm YES；缺参补齐后用同一 python 命令重试
"""
    )
    parser.add_argument("--due-date", type=int, help="到期日期（yyyyMMdd）；不传默认 20991231（长期有效）")
    parser.add_argument("--name", type=str, help="被分享人姓名（可选，用于展示/通知）")
    parser.add_argument("--no-notice", action="store_true", help="不发送钉钉分享通知（默认发送）")
    parser.add_argument("--source", type=str, help="生成短链的 source（可选，配合 --print-share-url）")
    parser.add_argument("--print-share-url", action="store_true", help="成功后额外输出 shareUrl")
    add_safety_args(parser)
    args = parser.parse_args()

    perms = parse_permissions(args.permissions) or DEFAULT_PERMISSIONS
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
