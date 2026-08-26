#!/usr/bin/env python3
"""
share / getMySharePermissions 脚本

用途：查询调用方对指定 fileId 的“可分享权限上限子集”（用于授权分享前的预检）

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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/share/getMySharePermissions"


def call_api(file_id: int) -> dict:
    params = [("fileId", str(file_id))]
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"
    return request_open_api(url, method="GET")

def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result

def main():
    parser = DocdbArgumentParser(description="查询我对该文件的分享权限", hint="""get-my-share-permissions.py 必须提供 file_id。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-my-share-permissions argv=["12345"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    args = parser.parse_args()

    result = call_api(args.file_id)
    processed = process_result(result)
    print(json.dumps(processed, ensure_ascii=False))

if __name__ == "__main__":
    main()

