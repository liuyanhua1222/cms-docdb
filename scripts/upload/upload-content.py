#!/usr/bin/env python3
"""
upload / uploadContent 脚本

用途：一键快速保存纯文本内容到个人知识库（AI 内容入库首选）

使用方式：
  python3 scripts/upload/upload-content.py

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

# 接口完整 URL（与 openapi/upload/upload-content.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/uploadContent"
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


def call_api(content: str, file_name: str,
             file_suffix: str = None, folder_name: str = None) -> dict:
    """调用一键上传接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {
        "content": content,
        "fileName": file_name
    }
    if file_suffix:
        body["fileSuffix"] = file_suffix
    if folder_name:
        body["folderName"] = folder_name

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
    parser = argparse.ArgumentParser(description="一键保存纯文本内容到个人知识库")
    parser.add_argument("content", type=str, help="文件内容")
    parser.add_argument("file_name", type=str, help="文件名（建议带扩展名）")
    parser.add_argument("--file-suffix", type=str, help="文件后缀（md/html/txt/json）")
    parser.add_argument("--folder-name", type=str, help="逻辑目录路径，支持多级")
    args = parser.parse_args()

    result = call_api(
        content=args.content,
        file_name=args.file_name,
        file_suffix=args.file_suffix,
        folder_name=args.folder_name
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
