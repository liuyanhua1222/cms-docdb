#!/usr/bin/env python3
"""
browse / getProjectList 脚本

用途：获取当前账号有权限访问的所有空间列表

使用方式：
  python3 scripts/browse/get-project-list.py [--name-key "关键词"] [--biz-code pmo]

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


# 接口完整 URL（与 openapi/browse/get-project-list.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/project/list"
AUTH_MODE = "appKey"


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


def call_api(app_code: str = None, name_key: str = None, biz_code: str = None) -> dict:
    """调用获取空间列表接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = []
    if app_code:
        params.append(("appCode", app_code))
    if name_key:
        params.append(("nameKey", name_key))
    if biz_code:
        params.append(("bizCode", biz_code))

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

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
    parser = argparse.ArgumentParser(description="获取当前账号有权限访问的空间列表")
    parser.add_argument("--app-code", type=str, help="应用编码（默认 kz_doc）")
    parser.add_argument("--name-key", type=str, help="空间名称模糊搜索关键词")
    parser.add_argument("--biz-code", type=str, help="业务线编码过滤")
    args = parser.parse_args()

    result = call_api(
        app_code=args.app_code,
        name_key=args.name_key,
        biz_code=args.biz_code
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
