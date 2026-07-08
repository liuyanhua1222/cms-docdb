#!/usr/bin/env python3
"""GET /document-database/admin/isProjectMember — 判断当前用户是否空间成员"""
import sys, os, json, urllib.request, urllib.parse, ssl, argparse
API_BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/admin/isProjectMember"

def headers():
    h = {"Content-Type": "application/json"}
    k = os.environ.get("appkey")
    if not k:
        print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr); sys.exit(1)
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("project_id", type=int)
    args = p.parse_args()
    url = f"{API_BASE}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers(), method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
