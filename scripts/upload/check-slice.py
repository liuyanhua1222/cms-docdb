#!/usr/bin/env python3
"""
upload / check-slice 脚本

用途：大文件分片上传前的 MD5 预检，支持秒传判定

使用方式：

"""

import sys
import urllib.parse
import os
import json

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/upload/check-slice.md 中声明的一致）
API_PATH = "/document-database/file/getSliceIdByMd5V2"


def call_api(md5: str, size: int = None, suffix: str = None) -> dict:
    """调用分片预检接口，返回原始 JSON 响应"""
    
    params = [("md5", md5)]
    if size is not None:
        params.append(("size", str(size)))
    if suffix:
        params.append(("suffix", suffix))

    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"

    return request_open_api(url, method="GET")

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
    parser = DocdbArgumentParser(description="大文件分片预检（支持秒传判定）",
        hint="""check-slice.py 必须提供 md5；真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/upload/check-slice.py "md5hex" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("md5", type=str, help="文件/分片的 MD5（hex 字符串）")
    parser.add_argument("--size", type=int, help="文件总大小（字节）")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    add_safety_args(parser)
    args = parser.parse_args()

    params = [("md5", args.md5)]
    if args.size is not None:
        params.append(("size", str(args.size)))
    if args.suffix:
        params.append(("suffix", args.suffix))
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"
    enforce_or_dry_run(args, method="GET", url=url, body=None)

    result = call_api(md5=args.md5, size=args.size, suffix=args.suffix)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
