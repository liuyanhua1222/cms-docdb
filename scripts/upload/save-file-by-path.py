#!/usr/bin/env python3
"""
upload / saveFileByPath 脚本

用途：将物理文件保存到指定项目空间的指定逻辑目录路径（路径不存在自动创建）

使用方式：
  python3 scripts/upload/save-file-by-path.py

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

# 接口完整 URL（与 openapi/upload/save-file-by-path.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/saveFileByPath"
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


def call_api(project_id: int, name: str, resource_id: int,
             path: str = None, suffix: str = None,
             size: int = None, is_sensitive: int = None) -> dict:
    """调用按路径保存文件接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {
        "projectId": project_id,
        "name": name,
        "fileType": "file",
        "resourceId": resource_id
    }
    if path:
        body["path"] = path
    if suffix:
        body["suffix"] = suffix
    if size is not None:
        body["size"] = size
    if is_sensitive is not None:
        body["isSensitive"] = is_sensitive

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
    parser = argparse.ArgumentParser(description="将物理文件保存到指定项目空间的指定路径")
    parser.add_argument("project_id", type=int, help="目标项目空间 ID")
    parser.add_argument("name", type=str, help="保存的文件名")
    parser.add_argument("resource_id", type=int, help="资源 ID（必须，先通过 upload-whole-file 获得）")
    parser.add_argument("--path", type=str, help="逻辑目录路径，支持多级，不存在自动创建")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件大小（字节）")
    parser.add_argument("--is-sensitive", type=int, choices=[0, 1], help="是否敏感文件（0 否，1 是）")
    args = parser.parse_args()

    result = call_api(
        project_id=args.project_id,
        name=args.name,
        resource_id=args.resource_id,
        path=args.path,
        suffix=args.suffix,
        size=args.size,
        is_sensitive=args.is_sensitive
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
