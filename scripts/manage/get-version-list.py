#!/usr/bin/env python3
"""
manage / getVersionList 脚本

用途：获取指定文件的完整版本历史列表。

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

API_PATH = "/document-database/file/getVersionList"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_INTERVAL = 1


def call_api(file_id: int) -> dict:
    return request_open_api(API_PATH, method="GET", params={"fileId": file_id})

def main() -> None:
    parser = DocdbArgumentParser(description="查看版本列表", hint="""get-version-list.py 必须提供 file_id。
示例: python3 -B <skill-dir>/scripts/manage/get-version-list.py 12345；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("file_id", type=int, help="文件 ID")
    args = parser.parse_args()

    result = call_api(args.file_id)
    versions = result.get("data") or []
    output = {
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": [
            {
                "id": v.get("id"),
                "fileId": v.get("fileId"),
                "versionNumber": v.get("versionNumber"),
                "versionName": v.get("versionName"),
                "status": v.get("status"),
                "remark": v.get("remark"),
                "creator": v.get("creator"),
                "createTime": v.get("createTime"),
                "lastVersion": v.get("lastVersion"),
            }
            for v in versions
        ] if isinstance(versions, list) else versions,
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
