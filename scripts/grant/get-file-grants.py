#!/usr/bin/env python3
"""GET /document-database/fileGrant/getGrants — 查询文件目录授权列表"""
import sys
import os
import json
import urllib.request
import urllib.parse
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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/getGrants"


def headers():
    return {"Content-Type": "application/json", "appKey": resolve_app_key()}


def main():
    parser = DocdbArgumentParser(description="查询目录授权列表", hint="get-file-grants.py 示例: ... 12345")
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    args = parser.parse_args()

    url = f"{API_URL}?{urllib.parse.urlencode([('fileId', str(args.file_id))])}"
    req = urllib.request.Request(url, headers=headers(), method="GET")
    ctx = ssl_context()
    with build_opener(ctx).open(req, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))


if __name__ == "__main__":
    main()
