#!/usr/bin/env python3
"""POST /document-database/fileGrant/upsertGrants — 增量目录授权（t_file_grant）"""
import sys, os, json, urllib.request, ssl, argparse
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/upsertGrants"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("appkey")
    if not k:
        print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file_id", type=int)
    p.add_argument("--emp-id", type=int, required=True)
    p.add_argument("--permissions", required=True, help="逗号分隔")
    p.add_argument("--due-date", type=int, default=20991231)
    args = p.parse_args()
    body = {
        "fileId": args.file_id,
        "grants": [{
            "empId": args.emp_id,
            "permissions": [x.strip() for x in args.permissions.split(",") if x.strip()],
            "dueDate": args.due_date,
        }],
    }
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
