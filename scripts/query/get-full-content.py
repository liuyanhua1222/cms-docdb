#!/usr/bin/env python3
"""
query / getFullFileContent 脚本

用途：获取文件的全局提纯文本（Markdown 格式），面向 AI 摘要/分析/RAG 消费

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

# 接口完整 URL（与 openapi/query/get-full-content.md 中声明的一致）
API_PATH = "/document-database/file/getFullFileContent"


def call_api(file_id: int, relation_id: str = None, file_type: str = None) -> dict:
    """调用全局提纯文本接口，返回原始 JSON 响应"""
    
    params = [("fileId", str(file_id))]
    if relation_id:
        params.append(("relationId", relation_id))
    if file_type:
        params.append(("fileType", file_type))

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
    parser = DocdbArgumentParser(
        description="获取文件全文内容（Markdown 格式）",
        hint="""get-full-content.py 必须提供 file_id。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-full-content argv=["12345"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--relation-id", type=str, help="业务关联 ID（可选）")
    parser.add_argument("--file-type", type=str, help="业务类型（可选，如 doc/file/work_report 等）")
    args = parser.parse_args()

    result = call_api(args.file_id, relation_id=args.relation_id, file_type=args.file_type)
    print(json.dumps(process_result(result), ensure_ascii=False))

if __name__ == "__main__":
    main()
