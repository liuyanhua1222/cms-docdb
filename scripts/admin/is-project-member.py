#!/usr/bin/env python3
"""GET /document-database/admin/isProjectMember — 判断当前用户是否空间成员"""
import sys, os, json, urllib.request, urllib.parse, argparse

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key
ensure_common_on_path(__file__)

API_BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/admin/isProjectMember"

def headers():
    h = {"Content-Type": "application/json"}
    k = resolve_app_key()
    h["appKey"] = k
    return h

def main():
    p = argparse.ArgumentParser()
    p.add_argument("project_id", type=int)
    args = p.parse_args()
    url = f"{API_BASE}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
    ctx = ssl_context()
    req = urllib.request.Request(url, headers=headers(), method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False))

if __name__ == "__main__":
    main()
