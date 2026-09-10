#!/usr/bin/env python3
"""GET /document-database/fileGrant/previewInheritChange — 切换权限继承前预检"""
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

API_PATH = "/document-database/fileGrant/previewInheritChange"


def main():
    parser = DocdbArgumentParser(
        description="切换权限继承前预检",
        hint="""preview-inherit-change.py 必须提供 --file-id 与 --cancel-inherit true|false。
示例: python3 -B <skill-dir>/scripts/grant/preview-inherit-change.py --file-id 12345 --cancel-inherit true
""",
    )
    parser.add_argument("--file-id", dest="file_id", required=True, type=int, help="文件夹 ID")
    parser.add_argument(
        "--cancel-inherit",
        required=True,
        choices=["true", "false"],
        help="目标：true=关闭继承；false=恢复继承",
    )
    args = parser.parse_args()
    q = urllib.parse.urlencode(
        [("fileId", str(args.file_id)), ("cancelInherit", args.cancel_inherit)]
    )
    result = request_open_api(f"{API_PATH}?{q}", method="GET")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
