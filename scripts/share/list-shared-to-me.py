#!/usr/bin/env python3
"""GET /document-database/share/sharedToMe — 分享给我的文件列表"""
import sys, os, json, urllib.request, urllib.parse, urllib.error, argparse

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
from docdb_open_api import ensure_common_on_path, ssl_context
ensure_common_on_path(__file__)

API_BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share/sharedToMe"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("appkey")
    if not k:
        print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--file-name", default=None)
    p.add_argument("--sharer-id", type=int, default=None)
    args = p.parse_args()
    q = [("pageIndex", str(args.page_index)), ("pageSize", str(args.page_size))]
    if args.file_name: q.append(("fileName", args.file_name))
    if args.sharer_id: q.append(("sharerId", str(args.sharer_id)))
    url = f"{API_BASE}?{urllib.parse.urlencode(q)}"
    ctx = ssl_context()
    req = urllib.request.Request(url, headers=headers(), method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
