#!/usr/bin/env python3
"""
upload / upload-whole-file 脚本

用途：上传本地完整文件（建议 20MB 以下），直接返回 resourceId

使用方式：
  python3 scripts/upload/upload-whole-file.py <file_path>

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import http.client
import urllib.parse
import uuid
import time

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key
ensure_common_on_path(__file__)
from safety import add_safety_args, enforce_or_dry_run

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


# 接口完整 URL（与 openapi/upload/upload-whole-file.md 中声明的一致）
API_HOST = "sg-al-cwork-web.mediportal.com.cn"
API_PATH = "/open-api/cwork-file/uploadWholeFile"
AUTH_MODE = "appKey"
CHUNK_SIZE = 5 * 1024 * 1024
MAX_RETRIES = 3
MAX_REDIRECTS = 5
RETRY_BACKOFF_SECONDS = (1, 2, 4)


class RetryableHttpError(Exception):
    """HTTP 状态码表示临时失败，可安全重试。"""


def build_app_key() -> str:
    """获取 appKey"""
    app_key = resolve_app_key()
    return app_key


def open_connection(scheme: str, host: str, ctx):
    if scheme == "http":
        return http.client.HTTPConnection(host, timeout=120)
    return http.client.HTTPSConnection(host, timeout=120, context=ctx)


def resolve_redirect(location: str, scheme: str, host: str, path: str):
    base_url = f"{scheme}://{host}{path}"
    target = urllib.parse.urljoin(base_url, location)
    parsed = urllib.parse.urlsplit(target)
    next_path = parsed.path or "/"
    if parsed.query:
        next_path = f"{next_path}?{parsed.query}"
    return parsed.scheme or scheme, parsed.netloc or host, next_path


def parse_response_body(status: int, body: bytes) -> dict:
    text = body.decode("utf-8", errors="replace")
    if status == 429 or status >= 500:
        raise RetryableHttpError(f"HTTP {status} - {text[:500]}")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "resultCode": 0,
            "resultMsg": f"HTTP {status} 返回非 JSON 响应: {text[:500]}",
            "data": None
        }


def send_upload_request(scheme: str, host: str, path: str, app_key: str,
                        boundary: str, header: bytes, footer: bytes,
                        content_length: int, file_path: str, ctx):
    conn = open_connection(scheme, host, ctx)
    try:
        conn.putrequest("POST", path)
        conn.putheader("appKey", app_key)
        conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
        conn.putheader("Content-Length", str(content_length))
        conn.endheaders()
        conn.send(header)
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                conn.send(chunk)
        conn.send(footer)
        return conn.getresponse()
    except Exception:
        conn.close()
        raise


def call_api(file_path: str) -> dict:
    """调用整传接口，返回原始 JSON 响应"""
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    app_key = build_app_key()

    boundary = uuid.uuid4().hex
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    content_length = len(header) + file_size + len(footer)

    for attempt in range(MAX_RETRIES):
        try:
            ctx = ssl_context()

            scheme = "https"
            host = API_HOST
            path = API_PATH

            for redirect_count in range(MAX_REDIRECTS + 1):
                resp = send_upload_request(
                    scheme, host, path, app_key, boundary, header, footer,
                    content_length, file_path, ctx
                )
                try:
                    if resp.status in (301, 302, 303, 307, 308):
                        location = resp.getheader("Location")
                        resp.read()
                        resp.close()
                        if not location:
                            raise RuntimeError(f"HTTP {resp.status} 重定向缺少 Location 响应头")
                        if redirect_count == MAX_REDIRECTS:
                            raise RuntimeError("重定向次数过多")
                        scheme, host, path = resolve_redirect(location, scheme, host, path)
                        continue

                    result = parse_response_body(resp.status, resp.read())
                    resp.close()
                    return result
                except RetryableHttpError:
                    resp.close()
                    raise
                except Exception as e:
                    resp.close()
                    return {
                        "resultCode": 0,
                        "resultMsg": str(e),
                        "data": None
                    }
        except RetryableHttpError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
            else:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
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
    parser = argparse.ArgumentParser(description="上传完整文件到知识库")
    parser.add_argument("file_path", type=str, nargs='?', help="文件路径（位置参数）")
    parser.add_argument("--file-path", type=str, dest="file_path_opt", help="文件路径（命名参数）")
    add_safety_args(parser)
    args = parser.parse_args()
    
    file_path = args.file_path or args.file_path_opt
    if file_path is None:
        print("错误: 请提供文件路径", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(file_path):
        print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    upload_url = f"https://{API_HOST}{API_PATH}"
    enforce_or_dry_run(
        args,
        method="POST",
        url=upload_url,
        body={"filePath": file_path, "fileName": os.path.basename(file_path)},
    )

    result = call_api(file_path)
    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
