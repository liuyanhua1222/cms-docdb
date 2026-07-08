#!/usr/bin/env python3
"""
share / getShareUrl 脚本

用途：生成文件/文件夹的“可转发预览短链接”（授权分享后用于链接分发）

使用方式：
  python3 scripts/share/get-share-url.py <file_id> [--source "external"]

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
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
    handlers = [CustomRedirectHandler()]
    if ctx:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share/getShareUrl"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if AUTH_MODE == "appKey":
        app_key = os.environ.get("appkey")
        if not app_key:
            print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr)
            sys.exit(1)
        headers["appKey"] = app_key
    return headers


def call_api(file_id: int, source: str = None) -> dict:
    headers = build_headers()
    params = [("fileId", str(file_id))]
    if source:
        params.append(("source", source))
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

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
    import argparse

    parser = argparse.ArgumentParser(description="生成文件/文件夹分享预览短链接（getShareUrl）")
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    parser.add_argument("--source", type=str, help="来源标识（可选）")
    args = parser.parse_args()

    result = call_api(args.file_id, source=args.source if args.source else None)
    processed = process_result(result)
    print(json.dumps(processed, ensure_ascii=False))


if __name__ == "__main__":
    main()

