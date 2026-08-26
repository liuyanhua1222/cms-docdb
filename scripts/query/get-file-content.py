#!/usr/bin/env python3
"""
query / getFileContent 脚本

用途：分页获取文件的文本内容，用于大文件的分段流式读取

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

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/query/get-file-content.md 中声明的一致）
API_PATH = "/document-database/file/getFileContent"


def call_api(file_id: int, page_number: int = 1) -> dict:
    """调用分页获取文件内容接口，返回原始 JSON 响应"""
    
    params = [("fileId", str(file_id)), ("pageNumber", str(page_number))]
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
    parser = DocdbArgumentParser(description="分页获取文件内容", hint="""get-file-content.py 必须提供 file_id。
示例: python3 -B <skill-dir>/scripts/query/get-file-content.py 12345；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--page-number", type=int, default=1, help="页码，从 1 开始")
    args = parser.parse_args()

    result = call_api(file_id=args.file_id, page_number=args.page_number)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
