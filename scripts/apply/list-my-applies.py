#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/myApplies — 我的申请列表"""
import sys, os, json, urllib.request, argparse

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key
ensure_common_on_path(__file__)

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/apply/myApplies"

def headers():
    h = {"Content-Type": "application/json"}
    k = resolve_app_key()
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--file-name", default=None)
    p.add_argument("--keyword", default=None, help="统一关键字，模糊匹配申请人姓名/文件名/申请事由")
    p.add_argument("--status", type=int, default=None)
    args = p.parse_args()
    body = {"pageIndex": args.page_index, "pageSize": args.page_size}
    if args.file_name: body["fileName"] = args.file_name
    if args.keyword: body["keyword"] = args.keyword
    if args.status is not None: body["status"] = args.status
    data = json.dumps(body).encode("utf-8")
    ctx = ssl_context()
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
