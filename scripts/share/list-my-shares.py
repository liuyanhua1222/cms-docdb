#!/usr/bin/env python3
"""GET /document-database/share/myShares — 我的分享列表"""
import sys, os, json, urllib.request, urllib.parse, ssl, argparse

API_BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share/myShares"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not k:
        print("错误: 请设置 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--file-name", default=None)
    args = p.parse_args()
    q = [("pageIndex", str(args.page_index)), ("pageSize", str(args.page_size))]
    if args.file_name: q.append(("fileName", args.file_name))
    url = f"{API_BASE}?{urllib.parse.urlencode(q)}"
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers(), method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
