#!/usr/bin/env python3
"""
browse / getMyRecentUsed 脚本

用途：分页查询当前用户最近使用记录（固定 file_online_read、file_download、upload2agent）

使用方式：
  python3 scripts/browse/get-my-recent-used.py [--page-index 1] [--page-size 20] [--biz-code pmo]

命令行参数：
  --appkey — 必填 CLI；值取自会话用户消息上下文 CMS_CWORK_APPKEY
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import argparse

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key, build_opener
ensure_common_on_path(__file__)
from cli_args import add_appkey_argument

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/operationLog/getMyRecentUsed"


def headers():
    h = {}
    k = resolve_app_key()
    h["appKey"] = k
    return h


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--biz-code", default=None)
    add_appkey_argument(p)
    args = p.parse_args()
    q = [("pageIndex", str(args.page_index)), ("pageSize", str(args.page_size))]
    if args.biz_code:
        q.append(("bizCode", args.biz_code))
    url = f"{API_URL}?{urllib.parse.urlencode(q)}"
    ctx = ssl_context()
    req = urllib.request.Request(url, headers=headers(), method="GET")
    with build_opener(ctx).open(req, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))


if __name__ == "__main__":
    main()
