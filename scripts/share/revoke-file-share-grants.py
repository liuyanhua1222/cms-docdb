#!/usr/bin/env python3
"""
share / revokeFileShareGrants 脚本

用途：整单撤销指定员工的协同分享（人从分享列表消失；幂等；不发送钉钉通知）。

勿用于「去掉 fileshare/预览/下载等单项权限」——请用 strip-share-permissions.py。

使用方式：

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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/share/revokeFileShareGrants"


def call_api(file_id: int, emp_ids: list) -> dict:
    body = {"fileId": file_id, "empIds": emp_ids}
    return request_open_api(API_PATH, method="POST", body=body)
def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result

def parse_emp_ids(raw: str) -> list:
    parts = [p.strip() for p in raw.split(",")]
    ids = []
    for p in parts:
        if not p:
            continue
        ids.append(int(p))
    if not ids:
        print("错误: --emp-ids 不能为空", file=sys.stderr)
        sys.exit(1)
    return ids

def main():
    parser = DocdbArgumentParser(description="撤销协同分享", hint="""revoke-file-share-grants.py 必须提供 file_id，且必须带 --emp-ids。
真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/share/revoke-file-share-grants.py 12345 --emp-ids "1,2" --confirm YES；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    parser.add_argument("--emp-ids", type=str, required=True, help="员工 empId 列表，逗号分隔")
    add_safety_args(parser)
    args = parser.parse_args()

    emp_ids = parse_emp_ids(args.emp_ids)
    body = {"fileId": args.file_id, "empIds": emp_ids}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = call_api(args.file_id, emp_ids)
    print(json.dumps(process_result(result), ensure_ascii=False))

if __name__ == "__main__":
    main()
