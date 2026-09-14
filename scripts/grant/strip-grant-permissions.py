#!/usr/bin/env python3
"""
grant / strip-grant-permissions 脚本

用途：从目录授权中去掉指定权限位（保留 read）；调用服务端 stripGrants 原子减权。

使用方式：
  python3 -B <skill-dir>/scripts/grant/strip-grant-permissions.py --file-id 12345 --emp-id 1 --remove "download" --confirm YES

"""

import sys
import os
import json
import time

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

URL_GET = "/document-database/fileGrant/getGrants"
URL_STRIP = "/document-database/fileGrant/stripGrants"
READ_PERM = "read"
MAX_CONFLICT_RETRIES = 2


def call_json(method: str, url: str, body: dict = None, params: list = None) -> dict:
    return request_open_api(url, method=method, body=body, params=params)


def parse_csv(raw: str) -> list:
    return [p.strip() for p in raw.split(",") if p.strip()]


def current_permissions(grant_entry: dict) -> set:
    """从目录授权条目提取有效权限 type（status==0 或未标 status）。"""
    raw = grant_entry.get("permissions")
    if isinstance(raw, list):
        out = set()
        for item in raw:
            if isinstance(item, dict):
                status = item.get("status")
                if status is not None and status != 0:
                    continue
                t = item.get("type") or item.get("permission")
                if t:
                    out.add(str(t).strip())
            elif item:
                out.add(str(item).strip())
        return {p for p in out if p}
    if isinstance(raw, str) and raw.strip():
        return {p.strip() for p in raw.split(",") if p.strip()}
    return set()


def fetch_before(file_id: int, emp_id: int):
    grants_resp = call_json("GET", f"{URL_GET}?fileId={file_id}")
    grants = grants_resp.get("data") if isinstance(grants_resp, dict) else None
    if not isinstance(grants, list):
        return None, grants_resp
    for item in grants:
        if isinstance(item, dict) and item.get("id") == emp_id:
            return current_permissions(item), grants_resp
    return set(), grants_resp


def is_conflict(result: dict) -> bool:
    if not isinstance(result, dict):
        return False
    msg = str(result.get("resultMsg") or "")
    code = result.get("resultCode")
    return "授权已变更" in msg or "grant_version_conflict" in msg.lower() or code == "GRANT_VERSION_CONFLICT"


def main():
    parser = DocdbArgumentParser(
        description="去掉目录授权中的指定权限位（保留 read；服务端原子减权）",
        hint="""strip-grant-permissions.py 必须提供 --file-id、--emp-id、--remove；真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/grant/strip-grant-permissions.py --file-id 12345 --emp-id 1 --remove "download" --confirm YES；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("--file-id", dest="file_id", required=True, type=int)
    parser.add_argument("--emp-id", type=int, required=True)
    parser.add_argument("--remove", type=str, required=True)
    parser.add_argument("--due-date", type=int, help="已忽略：减权保留原到期日")
    add_safety_args(parser)
    args = parser.parse_args()

    to_remove = set(parse_csv(args.remove))
    if READ_PERM in to_remove:
        print("错误: 不能通过本脚本移除 read；若要完全收回授权请用 revoke-file-grants.py", file=sys.stderr)
        sys.exit(1)
    if not to_remove:
        print("错误: --remove 不能为空", file=sys.stderr)
        sys.exit(1)

    # dry-run 必须是离线预览：不得为了计算 before/after 发起远程查询。
    if getattr(args, "dry_run", False):
        body = {
            "fileId": args.file_id,
            "items": [{"empId": args.emp_id, "removePermissions": sorted(to_remove),
                       "expectedPermissions": None}],
        }
        enforce_or_dry_run(args, method="POST", url=URL_STRIP, body=body)
        return

    before, grants_resp = fetch_before(args.file_id, args.emp_id)
    if before is None:
        print(json.dumps(grants_resp, ensure_ascii=False))
        sys.exit(1)
    if not before:
        print(json.dumps({"resultCode": 0, "resultMsg": "该员工无目录授权记录或无直接授权", "data": None}, ensure_ascii=False))
        sys.exit(1)

    after_local = before - to_remove
    after_local.add(READ_PERM)
    if before == after_local:
        print(json.dumps({
            "resultCode": 1,
            "resultMsg": "幂等：指定权限已不存在",
            "data": {"before": sorted(before), "after": sorted(after_local)},
        }, ensure_ascii=False))
        return

    # 服务端 strip：剔除 remove，并强制保留 read（与旧 Skill 语义一致）
    remove_list = sorted(to_remove)
    last_result = None
    for attempt in range(MAX_CONFLICT_RETRIES + 1):
        before, _ = fetch_before(args.file_id, args.emp_id)
        if before is None:
            before = set()
        body = {
            "fileId": args.file_id,
            "items": [{
                "empId": args.emp_id,
                "removePermissions": remove_list,
                "expectedPermissions": sorted(before),
            }],
        }
        enforce_or_dry_run(args, method="POST", url=URL_STRIP, body=body)
        if getattr(args, "dry_run", False):
            return
        last_result = call_json("POST", URL_STRIP, body=body)
        if not is_conflict(last_result):
            break
        if attempt >= MAX_CONFLICT_RETRIES:
            print(json.dumps({
                "resultCode": last_result.get("resultCode"),
                "resultMsg": "授权冲突重试耗尽，请勿盲重试：" + str(last_result.get("resultMsg")),
                "data": last_result.get("data"),
            }, ensure_ascii=False))
            sys.exit(1)
        time.sleep(0.2 * (attempt + 1))

    data = last_result.get("data") if isinstance(last_result, dict) else None
    print(json.dumps({
        "resultCode": last_result.get("resultCode") if isinstance(last_result, dict) else None,
        "resultMsg": last_result.get("resultMsg") if isinstance(last_result, dict) else None,
        "data": data,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
