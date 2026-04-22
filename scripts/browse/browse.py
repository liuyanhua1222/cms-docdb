#!/usr/bin/env python3
"""
browse / browse 脚本

用途：浏览指定目录下的直接子项（文件和文件夹）

使用方式：
  python3 scripts/browse/browse.py

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

# 接口完整 URL（与 openapi/browse/browse.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getChildFiles"
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


def call_api(parent_id: int, type: int = None, order: int = None,
             exclude_file_types: str = None, exclude_folder_names: str = None,
             return_file_desc: bool = True) -> dict:
    """调用浏览目录接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = [("parentId", str(parent_id))]
    if type is not None:
        params.append(("type", str(type)))
    if order is not None:
        params.append(("order", str(order)))
    if exclude_file_types:
        params.append(("excludeFileTypes", exclude_file_types))
    if exclude_folder_names:
        params.append(("excludeFolderNames", exclude_folder_names))
    if return_file_desc:
        params.append(("returnFileDesc", "true"))

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
    parser = argparse.ArgumentParser(description="浏览目录下的文件和文件夹")
    parser.add_argument("parent_id", type=int, help="父目录 ID（根目录传 0）")
    parser.add_argument("--type", type=int, choices=[1, 2], help="1 只查文件夹，2 只查文件")
    parser.add_argument("--order", type=int, choices=[1, 2, 3, 4, 5, 6], help="排序规则")
    parser.add_argument("--exclude-file-types", type=str, help="排除的文件类型，逗号分隔")
    parser.add_argument("--exclude-folder-names", type=str, help="排除的文件夹名称，逗号分隔")
    parser.add_argument("--no-return-file-desc", action="store_true", help="不返回文件描述")
    args = parser.parse_args()

    result = call_api(
        parent_id=args.parent_id,
        type=args.type,
        order=args.order,
        exclude_file_types=args.exclude_file_types,
        exclude_folder_names=args.exclude_folder_names,
        return_file_desc=not args.no_return_file_desc
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
