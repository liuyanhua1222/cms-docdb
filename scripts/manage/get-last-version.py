#!/usr/bin/env python3
"""
manage / getLastVersion 脚本

用途：快速获取文件当前最新版本的详细信息。

使用方式：
  python3 scripts/manage/get-last-version.py <file_id>

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error
import urllib.parse

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
from cli_args import DocdbArgumentParser

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    """自定义重定向处理器，显式支持 307/308 重定向并保留请求方法和请求体"""
    
    def http_error_301(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_302(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_303(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_307(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_308(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)


def build_opener(ctx):
    """构建支持 307/308 重定向的自定义 opener"""
    handlers = [CustomRedirectHandler()]
    if ctx:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getLastVersion"
AUTH_MODE = "appKey"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_INTERVAL = 1


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    app_key = resolve_app_key()
    headers["appKey"] = app_key
    return headers


def call_api(file_id: int) -> dict:
    headers = build_headers()
    params = urllib.parse.urlencode({"fileId": file_id})
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    ctx = ssl_context()

    opener = build_opener(ctx)

    for attempt in range(MAX_RETRIES):
        try:
            with opener.open(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)
            else:
                print(f"错误: HTTP {e.code} - {e.reason}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_INTERVAL)
            else:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)


def main() -> None:
    parser = DocdbArgumentParser(description="查看最新版本", hint="""get-last-version.py 必须提供 file_id。
示例: python3 -B <skill-dir>/scripts/manage/get-last-version.py 12345""")
    parser.add_argument("file_id", type=int, help="文件 ID")
    args = parser.parse_args()

    result = call_api(args.file_id)
    v = result.get("data") or {}
    output = {
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": {
            "id": v.get("id"),
            "fileId": v.get("fileId"),
            "versionNumber": v.get("versionNumber"),
            "versionName": v.get("versionName"),
            "status": v.get("status"),
            "remark": v.get("remark"),
            "creator": v.get("creator"),
            "createTime": v.get("createTime"),
            "lastVersion": v.get("lastVersion"),
        } if isinstance(v, dict) else v,
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
