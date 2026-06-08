#!/usr/bin/env python3
"""POST /document-database/admin/addMember — 添加空间普通成员（role=0）"""
import sys, os, json, urllib.request, ssl, argparse

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/admin/addMember"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not k:
        print("错误: 请设置 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("project_id", type=int)
    p.add_argument("--employee-id", type=int, required=True)
    args = p.parse_args()
    body = {"projectId": args.project_id, "employeeId": args.employee_id}
    data = json.dumps(body).encode("utf-8")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, data=data, headers=headers(), method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
