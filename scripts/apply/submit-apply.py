#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/submit — 提交权限申请（须先 get-approvers 选择审批人）"""
import sys, os, json, urllib.request, ssl, argparse

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/apply/submit"

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
    p.add_argument("--permissions", required=True, help="逗号分隔，如 read,preview,download")
    p.add_argument("--reason", required=True)
    p.add_argument("--approver-ids", required=True, help="逗号分隔的 employeeId")
    p.add_argument("--due-date", type=int, default=20991231)
    args = p.parse_args()
    body = {
        "fileId": args.file_id,
        "permissions": [x.strip() for x in args.permissions.split(",") if x.strip()],
        "reason": args.reason,
        "approverIds": [int(x.strip()) for x in args.approver_ids.split(",") if x.strip()],
        "dueDate": args.due_date,
    }
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
