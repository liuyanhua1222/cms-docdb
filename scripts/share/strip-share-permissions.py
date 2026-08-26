#!/usr/bin/env python3
"""
share / strip-share-permissions 脚本

用途：从已有协同分享记录中去掉指定权限位（保留 read）；勿用于整单撤销协同。

使用方式：
"""

import sys
import urllib.parse
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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

BASE = "/document-database/share"
URL_GET_SHARES = f"{BASE}/getFileShares"
URL_UPSERT = f"{BASE}/upsertFileShareGrants"
DEFAULT_DUE_DATE = 20991231
READ_PERM = "read"




def call_json(method: str, url: str, body: dict = None, params: list = None) -> dict:
    return request_open_api(url, method=method, body=body, params=params)

def parse_csv(raw: str) -> list:
    return [p.strip() for p in raw.split(",") if p.strip()]


def normalize_permissions(raw) -> set:
    if isinstance(raw, list):
        return {str(p).strip() for p in raw if str(p).strip()}
    if isinstance(raw, str) and raw.strip():
        return {p.strip() for p in raw.split(",") if p.strip()}
    return set()


def main():
    parser = DocdbArgumentParser(
        description="去掉协同分享中的指定权限位（保留 read）",
        hint="""strip-share-permissions.py 必须提供 file_id、--emp-id、--remove；真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=strip-share-permissions argv=["12345", "--emp-id", "1", "--remove", "fileshare", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    parser.add_argument("--emp-id", type=int, required=True, help="被分享员工 empId")
    parser.add_argument("--remove", type=str, required=True, help="要去掉的权限，逗号分隔（不可含 read）")
    parser.add_argument("--due-date", type=int, help="到期日 yyyyMMdd；不传则沿用原值或 20991231")
    add_safety_args(parser)
    args = parser.parse_args()

    to_remove = set(parse_csv(args.remove))
    if READ_PERM in to_remove:
        print("错误: 不能通过本脚本移除 read；若要完全取消协同请用 revoke-file-share-grants.py", file=sys.stderr)
        sys.exit(1)
    if not to_remove:
        print("错误: --remove 不能为空", file=sys.stderr)
        sys.exit(1)

    shares_resp = call_json("GET", URL_GET_SHARES, params=[("fileId", str(args.file_id))])
    shares = shares_resp.get("data") if isinstance(shares_resp, dict) else None
    if not isinstance(shares, list):
        print(json.dumps(shares_resp, ensure_ascii=False))
        sys.exit(1)

    target = None
    for item in shares:
        if not isinstance(item, dict):
            continue
        if item.get("objectType") == "person" and item.get("objectId") == args.emp_id:
            target = item
            break

    if target is None:
        print(json.dumps({"resultCode": 0, "resultMsg": "该员工不在协同分享列表", "data": None}, ensure_ascii=False))
        sys.exit(1)

    before = normalize_permissions(target.get("permissions"))
    after = before - to_remove
    after.add(READ_PERM)
    if before == after:
        print(json.dumps({
            "resultCode": 1,
            "resultMsg": "幂等：指定权限已不存在",
            "data": {"before": sorted(before), "after": sorted(after)},
        }, ensure_ascii=False))
        return

    due_date = args.due_date if args.due_date is not None else target.get("dueDate") or DEFAULT_DUE_DATE
    body = {
        "fileId": args.file_id,
        "isSendNotice": False,
        "shareGrants": [{
            "empId": args.emp_id,
            "permissions": sorted(after),
            "dueDate": due_date,
            "name": target.get("name"),
        }],
    }

    enforce_or_dry_run(args, method="POST", url=URL_UPSERT, body=body)
    result = call_json("POST", URL_UPSERT, body=body)
    out = {
        "resultCode": result.get("resultCode") if isinstance(result, dict) else None,
        "resultMsg": result.get("resultMsg") if isinstance(result, dict) else None,
        "data": {
            "before": sorted(before),
            "after": sorted(after),
            "api": result.get("data") if isinstance(result, dict) else result,
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
