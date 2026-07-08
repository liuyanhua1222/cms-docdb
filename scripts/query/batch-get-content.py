#!/usr/bin/env python3
"""
query / batchGetContent 脚本

用途：批量获取多个文件的全文内容，减少 RAG 场景交互次数

使用方式：
  python3 scripts/query/batch-get-content.py "[{\"fileId\":123},{\"fileId\":456}]"

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    """自定义重定向处理器，显式支持 307/308 重定向并保留请求方法和请求体"""
    
    def http_error_301(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_302(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_303(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_307(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)
    
    def http_error_308(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)


def build_opener(ctx):
    """构建支持 307/308 重定向的自定义 opener"""
    handlers = [CustomRedirectHandler()]
    if ctx:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)


# 接口完整 URL（与 openapi/query/batch-get-content.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/ai/batchGetContent"
AUTH_MODE = "appKey"
DEFAULT_MAX_CHARS = 0
DEFAULT_MAX_CHARS_PER_FILE = 0
CONTENT_KEYS = {"content", "text", "markdown", "fullContent", "fileContent"}


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        app_key = os.environ.get("appkey")
        if not app_key:
            print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr)
            sys.exit(1)
        headers["appKey"] = app_key

    return headers


def call_api(files: list) -> dict:
    """调用批量获取文件内容接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = json.dumps({"files": files}).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers=headers,
        method="POST"
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    opener = build_opener(ctx)

    for attempt in range(3):
        try:
            with opener.open(req, timeout=60) as resp:
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


def truncate_content_fields(value, state, max_chars: int, max_chars_per_file: int):
    """截断内容字段，避免批量全文结果撑爆上层上下文或传输链路。"""
    if isinstance(value, dict):
        return {
            key: truncate_content_fields(val, state, max_chars, max_chars_per_file)
            if key not in CONTENT_KEYS
            else truncate_text(val, state, max_chars, max_chars_per_file)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [truncate_content_fields(item, state, max_chars, max_chars_per_file) for item in value]
    return value


def truncate_text(value, state, max_chars: int, max_chars_per_file: int):
    if not isinstance(value, str):
        return value
    if max_chars <= 0 and max_chars_per_file <= 0:
        return value

    per_file_limit = len(value) if max_chars_per_file <= 0 else max_chars_per_file
    remaining_total = len(value) if max_chars <= 0 else max(max_chars - state["used"], 0)
    keep = min(len(value), per_file_limit, remaining_total)
    state["used"] += keep

    if keep < len(value):
        omitted = len(value) - keep
        state["truncated"] = True
        state["omitted_chars"] += omitted
        return value[:keep] + f"\n\n[TRUNCATED: omitted {omitted} chars]"
    return value


def process_result(result, max_chars: int, max_chars_per_file: int):
    """处理 API 响应结果，优先按 resultCode、resultMsg、data 读取"""
    if isinstance(result, dict):
        # 优先读取 resultCode、resultMsg、data
        result_code = result.get('resultCode')
        result_msg = result.get('resultMsg')
        data = result.get('data')
        state = {"used": 0, "truncated": False, "omitted_chars": 0}
        data = truncate_content_fields(data, state, max_chars, max_chars_per_file)
        
        # 构建标准化输出
        processed = {
            'resultCode': result_code,
            'resultMsg': result_msg,
            'data': data,
            'truncated': state["truncated"],
            'omittedChars': state["omitted_chars"],
            'maxChars': max_chars,
            'maxCharsPerFile': max_chars_per_file
        }
        return processed
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="批量获取多个文件的全文内容")
    parser.add_argument("files_json", type=str, help='文件列表 JSON，如 [{"fileId":123},{"fileId":456}]')
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="内容字段总字符上限，<=0 表示不限制")
    parser.add_argument("--max-chars-per-file", type=int, default=DEFAULT_MAX_CHARS_PER_FILE, help="单个内容字段字符上限，<=0 表示不限制")
    args = parser.parse_args()

    files = json.loads(args.files_json)
    result = call_api(files)

    processed_result = process_result(result, args.max_chars, args.max_chars_per_file)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
