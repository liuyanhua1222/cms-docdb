#!/usr/bin/env python3
"""
upload / check-slice 脚本

用途：大文件分片上传前的 MD5 预检，支持秒传判定

使用方式：
  python3 scripts/upload/check-slice.py <md5> [--size 12345] [--suffix pdf]

命令行参数：
  --appkey — 必填 CLI；值取自会话用户消息上下文 CMS_CWORK_APPKEY
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
from cli_args import add_appkey_argument
from safety import add_safety_args, enforce_or_dry_run

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/upload/check-slice.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getSliceIdByMd5V2"
AUTH_MODE = "appKey"

def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        headers["appKey"] = resolve_app_key()
    return headers

def call_api(md5: str, size: int = None, suffix: str = None) -> dict:
    """调用分片预检接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = [("md5", md5)]
    if size is not None:
        params.append(("size", str(size)))
    if suffix:
        params.append(("suffix", suffix))

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
    parser = argparse.ArgumentParser(description="大文件分片预检（支持秒传判定）")
    parser.add_argument("md5", type=str, help="文件/分片的 MD5（hex 字符串）")
    parser.add_argument("--size", type=int, help="文件总大小（字节）")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    add_safety_args(parser)
    add_appkey_argument(parser)
    args = parser.parse_args()

    params = [("md5", args.md5)]
    if args.size is not None:
        params.append(("size", str(args.size)))
    if args.suffix:
        params.append(("suffix", args.suffix))
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    enforce_or_dry_run(args, method="GET", url=url, body=None)

    result = call_api(md5=args.md5, size=args.size, suffix=args.suffix)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
