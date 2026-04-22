#!/usr/bin/env python3
"""
manage / updateFileProperty 脚本

用途：更新文件属性（重命名/移动）

使用方式：
  python3 scripts/manage/update-file-property.py <file_id> [--new-name "新文件名"] [--target-parent-id 123]

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

# 接口完整 URL（与 openapi/manage/update-file-property.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/updateFileProperty"
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


def call_api(file_id: int, new_name: str = None, target_parent_id: int = None,
             cover: bool = None, auto_rename: bool = None) -> dict:
    """调用更新文件属性接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {"fileId": file_id}
    if new_name is not None:
        body["newName"] = new_name
    if target_parent_id is not None:
        body["targetParentId"] = target_parent_id
    if cover is not None:
        body["cover"] = cover
    if auto_rename is not None:
        body["autoRename"] = auto_rename

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
    parser = argparse.ArgumentParser(description="更新文件属性（重命名/移动）")
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--new-name", type=str, help="新文件名")
    parser.add_argument("--target-parent-id", type=int, help="目标父目录 ID")
    parser.add_argument("--cover", action="store_true", help="同名冲突时覆盖")
    parser.add_argument("--auto-rename", action="store_true", help="同名冲突时自动追加数字后缀")
    args = parser.parse_args()

    if not args.new_name and not args.target_parent_id:
        print("错误: 必须提供 --new-name 或 --target-parent-id 之一", file=sys.stderr)
        sys.exit(1)

    result = call_api(
        file_id=args.file_id,
        new_name=args.new_name,
        target_parent_id=args.target_parent_id,
        cover=args.cover if args.cover else None,
        auto_rename=args.auto_rename if args.auto_rename else None
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
