#!/usr/bin/env python3
"""
browse / getMyRecentUsed 脚本

用途：分页查询当前用户最近使用记录（固定 file_online_read、file_download、upload2agent）

使用方式：
  python3 scripts/browse/get-my-recent-used.py [--page-index 1] [--page-size 20] [--biz-code kz_doc]

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import ssl
import argparse

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/operationLog/getMyRecentUsed"


def headers():
    h = {}
    k = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not k:
        print("错误: 请设置 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
        sys.exit(1)
    h["appKey"] = k
    return h


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--biz-code", default=None)
    args = p.parse_args()
    q = [("pageIndex", str(args.page_index)), ("pageSize", str(args.page_size))]
    if args.biz_code:
        q.append(("bizCode", args.biz_code))
    url = f"{API_URL}?{urllib.parse.urlencode(q)}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers(), method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))


if __name__ == "__main__":
    main()
