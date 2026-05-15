#!/usr/bin/env python3
"""
upload / register-slice 脚本

用途：在分片物理上传到 MinIO 完成后，在服务端注册分片元信息，换取 sliceId

使用方式：
  python3 scripts/upload/register-slice.py <full_path> <md5> <size> <storage_type>

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
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


# 接口完整 URL（与 openapi/upload/register-slice.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/uploadFileSliceV2"
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
    parser = argparse.ArgumentParser(description="注册文件分片")
    parser.add_argument("file_path", type=str, nargs='?', help="文件完整路径（位置参数）")
    parser.add_argument("md5", type=str, nargs='?', help="文件 MD5（位置参数）")
    parser.add_argument("size", type=int, nargs='?', help="文件大小（位置参数）")
    parser.add_argument("storage_type", type=str, nargs='?', help="存储类型（位置参数）")
    parser.add_argument("--file-path", type=str, dest="file_path_opt", help="文件完整路径（命名参数）")
    parser.add_argument("--md5", type=str, dest="md5_opt", help="文件 MD5（命名参数）")
    parser.add_argument("--size", type=int, dest="size_opt", help="文件大小（命名参数）")
    parser.add_argument("--storage-type", type=str, dest="storage_type_opt", help="存储类型（命名参数）")
    args = parser.parse_args()
    
    file_path = args.file_path or args.file_path_opt
    md5 = args.md5 or args.md5_opt
    size = args.size or args.size_opt
    storage_type = args.storage_type or args.storage_type_opt
    
    if None in [file_path, md5, size, storage_type]:
        print("用法: python3 scripts/upload/register-slice.py <full_path> <md5> <size> <storage_type>", file=sys.stderr)
        sys.exit(1)

    result = call_api(file_path, md5, size, storage_type)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
