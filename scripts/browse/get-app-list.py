#!/usr/bin/env python3
"""
browse / listAllApps 脚本

用途：获取当前企业下用户可访问的知识库应用（产品通道）列表。
用于意图不明时先按企业收敛选项，再决定 project/list 的 appCode。

使用方式：
  python3 scripts/browse/get-app-list.py

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/app/listAll"
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


def call_api() -> dict:
    headers = build_headers()
    req = urllib.request.Request(API_URL, headers=headers, method="GET")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
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
    result = call_api()
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
