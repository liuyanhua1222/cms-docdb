#!/usr/bin/env python3
"""
upload / register-slice 脚本

用途：在分片物理上传到 MinIO 完成后，在服务端注册分片元信息，换取 sliceId

使用方式：
  python3 scripts/upload/register-slice.py <full_path> <md5> <size> <storage_type>

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.error

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


# 接口完整 URL（与 openapi/upload/register-slice.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/uploadFileSliceV2"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        headers["appKey"] = resolve_app_key()
    return headers


def call_api(file_path: str, md5: str, size: int, storage_type: str) -> dict:
    """调用注册分片接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {
        "filePath": file_path,
        "md5": md5,
        "size": size,
        "storageType": storage_type
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    ctx = ssl_context()

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
    parser = argparse.ArgumentParser(description="注册文件分片")
    parser.add_argument("file_path", type=str, nargs='?', help="文件完整路径（位置参数）")
    parser.add_argument("md5", type=str, nargs='?', help="文件 MD5（位置参数）")
    parser.add_argument("size", type=int, nargs='?', help="文件大小（位置参数）")
    parser.add_argument("storage_type", type=str, nargs='?', help="存储类型（位置参数）")
    parser.add_argument("--file-path", type=str, dest="file_path_opt", help="文件完整路径（命名参数）")
    parser.add_argument("--md5", type=str, dest="md5_opt", help="文件 MD5（命名参数）")
    parser.add_argument("--size", type=int, dest="size_opt", help="文件大小（命名参数）")
    parser.add_argument("--storage-type", type=str, dest="storage_type_opt", help="存储类型（命名参数）")
    add_safety_args(parser)
    args = parser.parse_args()
    
    file_path = args.file_path or args.file_path_opt
    md5 = args.md5 or args.md5_opt
    size = args.size or args.size_opt
    storage_type = args.storage_type or args.storage_type_opt
    
    if None in [file_path, md5, size, storage_type]:
        print("用法: python3 scripts/upload/register-slice.py <full_path> <md5> <size> <storage_type>", file=sys.stderr)
        sys.exit(1)

    body = {
        "filePath": file_path,
        "md5": md5,
        "size": size,
        "storageType": storage_type,
    }
    enforce_or_dry_run(args, method="POST", url=API_URL, body=body)

    result = call_api(file_path, md5, size, storage_type)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
