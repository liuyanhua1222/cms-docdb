#!/usr/bin/env python3
"""
manage / getLastVersion 脚本

用途：快速获取文件当前最新版本的详细信息。

使用方式：
  python3 scripts/manage/get-last-version.py <file_id>

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error
import urllib.parse
import ssl

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getLastVersion"
AUTH_MODE = "appKey"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_INTERVAL = 1


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not app_key:
        print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
        sys.exit(1)
    headers["appKey"] = app_key
    return headers


def call_api(file_id: int) -> dict:
    headers = build_headers()
    params = urllib.parse.urlencode({"fileId": file_id})
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=TIMEOUT) as resp:
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
    parser = argparse.ArgumentParser(description="获取文件最新版本信息")
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
