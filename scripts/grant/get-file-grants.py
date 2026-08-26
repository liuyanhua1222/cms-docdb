#!/usr/bin/env python3
"""GET /document-database/fileGrant/getGrants — 查询文件目录授权列表"""
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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/fileGrant/getGrants"


def main():
    parser = DocdbArgumentParser(
        description="查询目录授权列表",
        hint="""get-file-grants.py 必须提供 file_id。
示例: python3 -B <skill-dir>/scripts/grant/get-file-grants.py 12345；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    args = parser.parse_args()

    url = f"{API_PATH}?{urllib.parse.urlencode([('fileId', str(args.file_id))])}"
    result = request_open_api(url, method="GET")
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
