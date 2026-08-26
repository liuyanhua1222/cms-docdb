#!/usr/bin/env python3
"""
browse / getRecentFiles 脚本

用途：获取当前用户最近上传的文件列表

使用方式：

"""

import sys
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

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/browse/get-recent-files.md 中声明的一致）
API_PATH = "/document-database/project/personal/getRecentFiles"


def call_api(limit: int = None, search_key: str = None) -> dict:
    """调用获取最近文件接口，返回原始 JSON 响应"""
    
    body = {}
    if limit is not None:
        body["limit"] = limit
    if search_key:
        body["searchKey"] = search_key

    return request_open_api(API_PATH, method="POST", body=body)

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
    parser = DocdbArgumentParser(description="获取当前用户最近上传的文件列表",
        hint="""get-recent-files.py get-recent-files 按业务参数调用（无必填时可传空 argv）。
示例: python3 -B <skill-dir>/scripts/browse/get-recent-files.py --limit 10；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("--limit", type=int, help="返回数量限制")
    parser.add_argument("--search-key", type=str, help="搜索关键词")
    args = parser.parse_args()

    result = call_api(limit=args.limit, search_key=args.search_key)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
