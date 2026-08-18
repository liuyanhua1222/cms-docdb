#!/usr/bin/env python3
"""
browse / getUploadableList 脚本

用途：获取当前账号有上传/编辑权限的空间列表

使用方式：
  python3 scripts/browse/get-uploadable-list.py [--name-key "关键词"] [--biz-code pmo]

运行时变量：
  CMS_CWORK_APPKEY — 由会话用户消息上下文提供，执行时注入为进程环境变量
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
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key, build_opener
ensure_common_on_path(__file__)

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/browse/get-uploadable-list.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/project/uploadableList"
AUTH_MODE = "appKey"

def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        headers["appKey"] = resolve_app_key()
    return headers

def call_api(app_code: str = None, name_key: str = None, biz_code: str = None) -> dict:
    """调用获取有上传权限空间列表接口，返回原始 JSON 响应"""
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
    parser = argparse.ArgumentParser(description="获取当前账号有上传/编辑权限的空间列表")
    parser.add_argument("--app-code", type=str, help="应用编码")
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
