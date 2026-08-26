#!/usr/bin/env python3
"""
share / searchEmpByName 脚本

用途：按姓名/关键词搜索员工，获取 empId（inside.empList[].id）

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

API_PATH = "/cwork-user/searchEmpByName"


def call_api(search_key: str) -> dict:
    
    params = [("searchKey", search_key)]
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
    parser = DocdbArgumentParser(
        description="按姓名搜索员工",
        hint=(
            "search-emp-by-name.py 必须提供 search_key。\n"
            "示例: python3 -B <skill-dir>/scripts/share/search-emp-by-name.py；缺参补齐后用同一 python 命令重试"
        ),
    )
    parser.add_argument("search_key", type=str, help="搜索关键词（姓名等；中文会自动 URL 编码）")
    args = parser.parse_args()

    result = call_api(args.search_key)
    processed = process_result(result)
    print(json.dumps(processed, ensure_ascii=False))

if __name__ == "__main__":
    main()

