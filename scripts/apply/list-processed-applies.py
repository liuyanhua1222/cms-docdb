#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/processed — 我已处理的申请"""
import sys, os, json, urllib.request, ssl, argparse

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/apply/processed"

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
    p.add_argument("--keyword", default=None, help="统一关键字，模糊匹配申请人姓名/文件名/申请事由")
    p.add_argument("--status", type=int, default=None, help="2=通过 3=拒绝")
    args = p.parse_args()
    body = {"pageIndex": args.page_index, "pageSize": args.page_size}
    if args.file_name: body["fileName"] = args.file_name
    if args.keyword: body["keyword"] = args.keyword
    if args.status is not None: body["status"] = args.status
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
