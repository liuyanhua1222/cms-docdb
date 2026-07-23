#!/usr/bin/env python3
"""
upload / get-file-download-info 脚本

用途：根据 resourceId 获取文件下载信息（临时下载 URL，有效期 1 小时）

使用方式：
  python3 scripts/upload/get-file-download-info.py <resource_id>

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.parse
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


# 接口完整 URL（与 openapi/upload/get-file-download-info.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/cwork-file/getDownloadInfo"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        headers["appKey"] = resolve_app_key()
    return headers


def call_api(resource_id: int) -> dict:
    """调用获取文件下载信息接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = [("resourceId", str(resource_id))]
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="获取文件下载信息（临时下载 URL）")
    parser.add_argument("resource_id", type=int, nargs='?', help="资源 ID（位置参数）")
    parser.add_argument("--resource-id", type=int, dest="resource_id_opt", help="资源 ID（命名参数）")
    args = parser.parse_args()
    
    resource_id = args.resource_id or args.resource_id_opt
    if resource_id is None:
        print("错误: 请提供 resourceId", file=sys.stderr)
        sys.exit(1)

    result = call_api(resource_id)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
