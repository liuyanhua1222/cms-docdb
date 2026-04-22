#!/usr/bin/env python3
"""
browse / getRecentFiles 脚本

用途：获取当前用户最近上传的文件列表

使用方式：
  python3 scripts/browse/get-recent-files.py [--limit 10] [--search-key "关键词"]

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

# 接口完整 URL（与 openapi/browse/get-recent-files.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/project/personal/getRecentFiles"
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


def call_api(limit: int = None, search_key: str = None) -> dict:
    """调用获取最近文件接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {}
    if limit is not None:
        body["limit"] = limit
    if search_key:
        body["searchKey"] = search_key

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8") if body else None,
        headers=headers,
        method="POST"
    )

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
    """处理 API 响应结果，优先按 resultCode、resultMsg、data 读取"""
    if isinstance(result, dict):
        # 优先读取 resultCode、resultMsg、data
        result_code = result.get('resultCode')
        result_msg = result.get('resultMsg')
        data = result.get('data')
        
        # 构建标准化输出
        processed = {
            'resultCode': result_code,
            'resultMsg': result_msg,
            'data': data
        }
        return processed
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="获取当前用户最近上传的文件列表")
    parser.add_argument("--limit", type=int, help="返回数量限制")
    parser.add_argument("--search-key", type=str, help="搜索关键词")
    args = parser.parse_args()

    result = call_api(limit=args.limit, search_key=args.search_key)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
