#!/usr/bin/env python3
"""
upload / get-file-download-info 脚本

用途：根据 resourceId 获取文件下载信息（临时下载 URL，有效期 1 小时）

使用方式：
  python3 scripts/upload/get-file-download-info.py <resource_id>

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl

# 接口完整 URL（与 openapi/upload/get-file-download-info.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/getDownloadInfo"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
        if not app_key:
            print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
            sys.exit(1)
        headers["appKey"] = app_key

    return headers


def call_api(resource_id: int) -> dict:
    """调用获取文件下载信息接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = [("resourceId", str(resource_id))]
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

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


def main():
    if len(sys.argv) < 2:
        print("错误: 请提供 resourceId", file=sys.stderr)
        sys.exit(1)

    resource_id = int(sys.argv[1])

    result = call_api(resource_id)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
