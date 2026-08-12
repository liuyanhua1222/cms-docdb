#!/usr/bin/env python3
"""
grant / strip-grant-permissions 脚本

用途：从目录授权中去掉指定权限位（保留 read）；勿用于整单收回授权。

使用方式：
  python3 scripts/grant/strip-grant-permissions.py <file_id> --emp-id <emp_id> --remove download,preview --confirm YES
"""

import sys
import os
import json
import urllib.request
import urllib.error

_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key, build_opener
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

URL_GET = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/getGrants"
URL_UPSERT = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/upsertGrants"
DEFAULT_DUE_DATE = 20991231
READ_PERM = "read"


def headers():
    return {"Content-Type": "application/json", "appKey": resolve_app_key()}


def call_json(method: str, url: str, body: dict = None) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers(), method=method)
    ctx = ssl_context()
    with build_opener(ctx).open(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_csv(raw: str) -> list:
    return [p.strip() for p in raw.split(",") if p.strip()]


def current_permissions(grant_entry: dict) -> set:
    perms = set()
    for p in grant_entry.get("permissions") or []:
        if not isinstance(p, dict):
            continue
        if p.get("status") == 0 and p.get("type"):
            perms.add(str(p.get("type")).strip())
    return perms


def main():
    parser = DocdbArgumentParser(
        description="去掉目录授权中的指定权限位（保留 read）",
        hint="strip-grant-permissions.py 示例: ... 12345 --emp-id 1 --remove download --confirm YES",
    )
    parser.add_argument("file_id", type=int)
    parser.add_argument("--emp-id", type=int, required=True)
    parser.add_argument("--remove", type=str, required=True)
    parser.add_argument("--due-date", type=int)
    add_safety_args(parser)
    args = parser.parse_args()

    to_remove = set(parse_csv(args.remove))
    if READ_PERM in to_remove:
        print("错误: 不能通过本脚本移除 read；若要完全收回授权请用 revoke-file-grants.py", file=sys.stderr)
        sys.exit(1)
    if not to_remove:
        print("错误: --remove 不能为空", file=sys.stderr)
        sys.exit(1)

    grants_resp = call_json("GET", f"{URL_GET}?fileId={args.file_id}")
    grants = grants_resp.get("data") if isinstance(grants_resp, dict) else None
    if not isinstance(grants, list):
        print(json.dumps(grants_resp, ensure_ascii=False))
        sys.exit(1)

    target = None
    for item in grants:
        if isinstance(item, dict) and item.get("id") == args.emp_id:
            target = item
            break

    if target is None:
        print(json.dumps({"resultCode": 0, "resultMsg": "该员工无目录授权记录", "data": None}, ensure_ascii=False))
        sys.exit(1)

    before = current_permissions(target)
    if not before:
        print(json.dumps({"resultCode": 0, "resultMsg": "该员工在当前目录无直接授权（可能仅为继承）", "data": None}, ensure_ascii=False))
        sys.exit(1)

    after = before - to_remove
    after.add(READ_PERM)
    if before == after:
        print(json.dumps({
            "resultCode": 1,
            "resultMsg": "幂等：指定权限已不存在",
            "data": {"before": sorted(before), "after": sorted(after)},
        }, ensure_ascii=False))
        return

    due_date = args.due_date if args.due_date is not None else DEFAULT_DUE_DATE
    body = {
        "fileId": args.file_id,
        "grants": [{
            "empId": args.emp_id,
            "permissions": sorted(after),
            "dueDate": due_date,
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
