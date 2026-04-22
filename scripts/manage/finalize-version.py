#!/usr/bin/env python3
"""
manage / finalizeVersion 脚本

用途：将文件的某个版本标记为正式定稿状态（status 从 1 变为 2）。
      不传 version_number 则定稿最新版本。

使用方式：
  # 定稿最新版本
  python3 scripts/manage/finalize-version.py <file_id>

  # 定稿指定版本号
  python3 scripts/manage/finalize-version.py <file_id> --version-number 3

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
import ssl

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/finalizeVersion"
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


def call_api(payload: dict) -> dict:
    headers = build_headers()
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
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
    parser = argparse.ArgumentParser(description="将文件版本标记为定稿")
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--version-number", type=int, default=0,
                        help="要定稿的版本号（不传或传 0 则定稿最新版本）")
    args = parser.parse_args()

    payload = {"fileId": args.file_id}
    if args.version_number:
        payload["versionNumber"] = args.version_number

    result = call_api(payload)
    output = {
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": result.get("data"),
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
