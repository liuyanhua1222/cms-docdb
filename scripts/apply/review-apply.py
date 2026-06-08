#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/review — 审批权限申请（pass/refuse）"""
import sys, os, json, urllib.request, ssl, argparse

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/fileGrant/apply/review"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not k:
        print("错误: 请设置 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("apply_id", type=int)
    p.add_argument("--action", required=True, choices=["pass", "refuse"])
    p.add_argument("--permissions", default=None, help="pass 时：逗号分隔")
    p.add_argument("--due-date", type=int, default=20991231)
    p.add_argument("--reason", default=None, help="refuse 时必填")
    args = p.parse_args()
    body = {"applyId": args.apply_id, "action": args.action}
    if args.action == "pass":
        if not args.permissions:
            print("错误: pass 须指定 --permissions", file=sys.stderr); sys.exit(1)
        body["permissions"] = [x.strip() for x in args.permissions.split(",") if x.strip()]
        body["dueDate"] = args.due_date
    else:
        if not args.reason:
            print("错误: refuse 须指定 --reason", file=sys.stderr); sys.exit(1)
        body["reason"] = args.reason
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
