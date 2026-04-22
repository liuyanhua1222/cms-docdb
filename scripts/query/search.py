#!/usr/bin/env python3
"""
query / search 脚本

用途：根据关键词搜索文件或目录

使用方式：
  python3 scripts/query/search.py "搜索关键词"

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

# 接口完整 URL（与 openapi/query/search.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/searchFile"
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


def call_api(name_key: str, project_id: int = None, root_file_id: int = None,
             start_time: int = None, end_time: int = None,
             is_file_storage: bool = None,
             exclude_file_types: str = None, exclude_folder_names: str = None) -> dict:
    """调用文件搜索接口，返回原始 JSON 响应"""
    headers = build_headers()

    # nameKey 必须 URL 编码
    params = [("nameKey", name_key)]
    if project_id is not None:
        params.append(("projectId", str(project_id)))
    if root_file_id is not None:
        params.append(("rootFileId", str(root_file_id)))
    if start_time is not None:
        params.append(("startTime", str(start_time)))
    if end_time is not None:
        params.append(("endTime", str(end_time)))
    if is_file_storage is not None:
        params.append(("isFileStorage", "true" if is_file_storage else "false"))
    if exclude_file_types:
        params.append(("excludeFileTypes", exclude_file_types))
    if exclude_folder_names:
        params.append(("excludeFolderNames", exclude_folder_names))

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
    parser = argparse.ArgumentParser(description="搜索文件或目录")
    parser.add_argument("name_key", type=str, help="搜索关键词")
    parser.add_argument("--project-id", type=int, help="项目/空间 ID")
    parser.add_argument("--root-file-id", type=int, help="指定根目录 ID")
    parser.add_argument("--start-time", type=int, help="开始时间戳（毫秒）")
    parser.add_argument("--end-time", type=int, help="结束时间戳（毫秒）")
    parser.add_argument("--is-file-storage", action="store_true", help="文件存储范围")
    parser.add_argument("--exclude-file-types", type=str, help="排除的文件类型，逗号分隔")
    parser.add_argument("--exclude-folder-names", type=str, help="排除的文件夹名称，逗号分隔")
    args = parser.parse_args()

    result = call_api(
        name_key=args.name_key,
        project_id=args.project_id,
        root_file_id=args.root_file_id,
        start_time=args.start_time,
        end_time=args.end_time,
        is_file_storage=args.is_file_storage,
        exclude_file_types=args.exclude_file_types,
        exclude_folder_names=args.exclude_folder_names
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
