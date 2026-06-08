#!/usr/bin/env python3
"""POST /document-database/fileGrant/revokeGrants — 收回目录授权"""
import sys, os, json, urllib.request, ssl, argparse

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/revokeGrants"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not k:
        print("错误: 请设置 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file_id", type=int)
    p.add_argument("--emp-ids", required=True, help="逗号分隔的 employeeId")
    args = p.parse_args()
    body = {
        "fileId": args.file_id,
        "employeeIds": [int(x.strip()) for x in args.emp_ids.split(",") if x.strip()],
    }
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
