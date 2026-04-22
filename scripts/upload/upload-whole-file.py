#!/usr/bin/env python3
"""
upload / upload-whole-file 脚本

用途：上传本地完整文件（建议 20MB 以下），直接返回 resourceId

使用方式：
  python3 scripts/upload/upload-whole-file.py <file_path>

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import http.client
import uuid
import ssl

# 接口完整 URL（与 openapi/upload/upload-whole-file.md 中声明的一致）
API_HOST = "sg-al-cwork-web.mediportal.com.cn"
API_PATH = "/open-api/cwork-file/uploadWholeFile"
AUTH_MODE = "appKey"


def build_app_key() -> str:
    """获取 appKey"""
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not app_key:
        print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
        sys.exit(1)
    return app_key


def call_api(file_path: str) -> dict:
    """调用整传接口，返回原始 JSON 响应"""
    app_key = build_app_key()

    filename = os.path.basename(file_path)
    boundary = uuid.uuid4().hex

    # 构造 multipart/form-data body
    with open(file_path, "rb") as f:
        file_content = f.read()

    body_parts = []

    # 文件字段
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    )
    body_parts.append(header.encode("utf-8"))
    body_parts.append(file_content)
    body_parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(body_parts)

    for attempt in range(3):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            conn = http.client.HTTPSConnection(API_HOST, timeout=120, context=ctx)
            try:
                conn.request(
                    "POST",
                    API_PATH,
                    body=body,
                    headers={
                        "appKey": app_key,
                        "Content-Type": f"multipart/form-data; boundary={boundary}",
                        "Content-Length": str(len(body)),
                    }
                )
                resp = conn.getresponse()
                result = json.loads(resp.read().decode("utf-8"))
                return result
            finally:
                conn.close()
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
    if len(sys.argv) < 2:
        print("错误: 请提供文件路径", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = call_api(file_path)
    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
