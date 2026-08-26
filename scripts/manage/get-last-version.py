#!/usr/bin/env python3
"""
manage / getLastVersion 脚本

用途：快速获取文件当前最新版本的详细信息。

使用方式：

"""

import sys
import urllib.parse
import os
import json
import time

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

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

API_PATH = "/document-database/file/getLastVersion"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_INTERVAL = 1


def call_api(file_id: int) -> dict:
    return request_open_api(API_PATH, method="GET", params={"fileId": file_id})

def main() -> None:
    parser = DocdbArgumentParser(description="查看最新版本", hint="""get-last-version.py 必须提供 file_id。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-last-version argv=["12345"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("file_id", type=int, help="文件 ID")
    args = parser.parse_args()

    result = call_api(args.file_id)
    v = result.get("data") or {}
    output = {
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": {
            "id": v.get("id"),
            "fileId": v.get("fileId"),
            "versionNumber": v.get("versionNumber"),
            "versionName": v.get("versionName"),
            "status": v.get("status"),
            "remark": v.get("remark"),
            "creator": v.get("creator"),
            "createTime": v.get("createTime"),
            "lastVersion": v.get("lastVersion"),
        } if isinstance(v, dict) else v,
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
