#!/usr/bin/env python3
"""GET /document-database/fileGrant/getInheritPermission — 查询文件夹权限继承状态"""
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

API_PATH = "/document-database/fileGrant/getInheritPermission"


def main():
    parser = DocdbArgumentParser(
        description="查询文件夹权限继承状态",
        hint="""get-inherit-permission.py 必须提供 --file-id（文件夹）。
示例: python3 -B <skill-dir>/scripts/grant/get-inherit-permission.py --file-id 12345
""",
    )
    parser.add_argument("--file-id", dest="file_id", required=True, type=int, help="文件夹 ID")
    args = parser.parse_args()
    url = f"{API_PATH}?{urllib.parse.urlencode([('fileId', str(args.file_id))])}"
    result = request_open_api(url, method="GET")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
