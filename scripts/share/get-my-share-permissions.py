#!/usr/bin/env python3
"""
share / getMySharePermissions 脚本

用途：查询调用方对指定 fileId 的“可分享权限上限子集”（用于授权分享前的预检）

使用方式：
  python3 scripts/share/get-my-share-permissions.py <file_id>

命令行参数：
  --appkey — 必填 CLI；值取自会话用户消息上下文 CMS_CWORK_APPKEY
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error

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
from cli_args import DocdbArgumentParser

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share/getMySharePermissions"
AUTH_MODE = "appKey"

def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if AUTH_MODE == "appKey":
        headers["appKey"] = resolve_app_key()
    return headers

def call_api(file_id: int) -> dict:
    headers = build_headers()
    params = [("fileId", str(file_id))]
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers, method="GET")

    ctx = ssl_context()

    opener = build_opener(ctx)
    for attempt in range(3):
        try:
            with opener.open(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if attempt < 2:
                import time

                time.sleep(1)
            else:
                print(f"错误: HTTP {e.code} - {e.reason}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            if attempt < 2:
                import time

                time.sleep(1)
            else:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)

def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result

def main():
    parser = DocdbArgumentParser(description="查询我对该文件的分享权限", hint="""get-my-share-permissions.py 必须提供 file_id。
示例: python3 -B <skill-dir>/scripts/share/get-my-share-permissions.py 12345""")
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    args = parser.parse_args()

    result = call_api(args.file_id)
    processed = process_result(result)
    print(json.dumps(processed, ensure_ascii=False))

if __name__ == "__main__":
    main()

