#!/usr/bin/env python3
"""
manage / updateFileVersion 脚本

用途：将已上传的物理文件资源绑定到已有文件，产生新版本记录。

使用方式：
  python3 scripts/manage/update-file-version.py <file_id> <project_id> <resource_id> \
    [--version-status 3] [--version-name "V2.0"] [--version-remark "修订内容"] \
    [--suffix pdf] [--size 204800]

versionStatus 说明：
  1 = 覆盖当前草稿（默认）
  2 = 强制新建版本
  3 = 新建版本并立即定稿（推荐）

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

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/updateFileVersion"
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
    parser = argparse.ArgumentParser(description="物理文件版本更新")
    parser.add_argument("file_id", type=int, help="要更新的文件 ID")
    parser.add_argument("project_id", type=int, help="文件所在空间 ID")
    parser.add_argument("resource_id", type=int, help="新上传的物理资源 ID")
    parser.add_argument("--version-status", type=int, default=3,
                        help="版本行为：1=覆盖草稿，2=强制新建，3=新建并立即定稿（默认 3）")
    parser.add_argument("--version-name", type=str, help="版本名称，如 V2.0")
    parser.add_argument("--version-remark", type=str, help="版本说明")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件大小（字节）")
    args = parser.parse_args()

    payload = {
        "id": args.file_id,
        "projectId": args.project_id,
        "resourceId": args.resource_id,
        "versionStatus": args.version_status,
    }
    if args.version_name:
        payload["versionName"] = args.version_name
    if args.version_remark:
        payload["versionRemark"] = args.version_remark
    if args.suffix:
        payload["suffix"] = args.suffix
    if args.size:
        payload["size"] = args.size

    result = call_api(payload)
    output = {
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": result.get("data"),
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
