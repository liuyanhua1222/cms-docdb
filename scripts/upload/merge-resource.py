#!/usr/bin/env python3
"""
upload / merge-resource 脚本

用途：合并所有已注册的分片，生成最终的 resourceId

使用方式：
  python3 scripts/upload/merge-resource.py "文件名.pdf" "<slice_id1,slice_id2,..." [--suffix pdf] [--size 12345]

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

# 接口完整 URL（与 openapi/upload/merge-resource.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/saveResource"
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


def call_api(name: str, slice_ids: list, suffix: str = None, size: int = None) -> dict:
    """调用合并分片接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {
        "name": name,
        "sliceIds": slice_ids
    }
    if suffix:
        body["suffix"] = suffix
    if size is not None:
        body["size"] = size

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
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
    parser = argparse.ArgumentParser(description="合并分片生成最终 resourceId")
    parser.add_argument("name", type=str, help="文件名（含后缀）")
    parser.add_argument("slice_ids", type=str, help="分片 ID 列表，逗号分隔")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件总大小（字节）")
    args = parser.parse_args()

    slice_ids = [int(x.strip()) for x in args.slice_ids.split(",")]

    result = call_api(name=args.name, slice_ids=slice_ids, suffix=args.suffix, size=args.size)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
