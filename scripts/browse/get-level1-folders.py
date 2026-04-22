#!/usr/bin/env python3
"""
browse / getLevel1Folders 脚本

用途：拉取指定项目空间的根目录下的所有文件夹及文件

使用方式：
  python3 scripts/browse/get-level1-folders.py <project_id> [--order 1]

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

# 接口完整 URL（与 openapi/browse/get-level1-folders.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getLevel1Folders"
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


def call_api(project_id: int, order: int = None, permission_query: str = None) -> dict:
    """调用获取一级目录接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = [("projectId", str(project_id))]
    if order is not None:
        params.append(("order", str(order)))
    if permission_query:
        params.append(("permissionQuery", permission_query))

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
    parser = argparse.ArgumentParser(description="拉取指定项目空间的根目录内容")
    parser.add_argument("project_id", type=int, help="项目/空间 ID")
    parser.add_argument("--order", type=int, choices=[1, 2, 5, 6], help="排序规则：1 更新倒序，2 更新顺序，5 名字倒序，6 名字顺序")
    parser.add_argument("--permission-query", type=str, help="权限查询条件")
    args = parser.parse_args()

    result = call_api(
        project_id=args.project_id,
        order=args.order,
        permission_query=args.permission_query
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
