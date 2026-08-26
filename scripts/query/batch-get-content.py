#!/usr/bin/env python3
"""
query / batchGetContent 脚本

用途：批量获取多个文件的全文内容，减少 RAG 场景交互次数

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

# 接口完整 URL（与 openapi/query/batch-get-content.md 中声明的一致）
API_PATH = "/document-database/ai/batchGetContent"
DEFAULT_MAX_CHARS = 0
DEFAULT_MAX_CHARS_PER_FILE = 0
CONTENT_KEYS = {"content", "text", "markdown", "fullContent", "fileContent"}


def call_api(files: list) -> dict:
    """调用批量获取文件内容接口，返回原始 JSON 响应"""
    
    body = json.dumps({"files": files}).encode("utf-8")

    return request_open_api(API_PATH, method="POST", body=body)
def truncate_content_fields(value, state, max_chars: int, max_chars_per_file: int):
    """截断内容字段，避免批量全文结果撑爆上层上下文或传输链路。"""
    if isinstance(value, dict):
        return {
            key: truncate_content_fields(val, state, max_chars, max_chars_per_file)
            if key not in CONTENT_KEYS
            else truncate_text(val, state, max_chars, max_chars_per_file)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [truncate_content_fields(item, state, max_chars, max_chars_per_file) for item in value]
    return value

def truncate_text(value, state, max_chars: int, max_chars_per_file: int):
    if not isinstance(value, str):
        return value
    if max_chars <= 0 and max_chars_per_file <= 0:
        return value

    per_file_limit = len(value) if max_chars_per_file <= 0 else max_chars_per_file
    remaining_total = len(value) if max_chars <= 0 else max(max_chars - state["used"], 0)
    keep = min(len(value), per_file_limit, remaining_total)
    state["used"] += keep

    if keep < len(value):
        omitted = len(value) - keep
        state["truncated"] = True
        state["omitted_chars"] += omitted
        return value[:keep] + f"\n\n[TRUNCATED: omitted {omitted} chars]"
    return value

def process_result(result, max_chars: int, max_chars_per_file: int):
    """处理 API 响应结果，优先按 resultCode、resultMsg、data 读取"""
    if isinstance(result, dict):
        # 优先读取 resultCode、resultMsg、data
        result_code = result.get('resultCode')
        result_msg = result.get('resultMsg')
        data = result.get('data')
        state = {"used": 0, "truncated": False, "omitted_chars": 0}
        data = truncate_content_fields(data, state, max_chars, max_chars_per_file)
        
        # 构建标准化输出
        processed = {
            'resultCode': result_code,
            'resultMsg': result_msg,
            'data': data,
            'truncated': state["truncated"],
            'omittedChars': state["omitted_chars"],
            'maxChars': max_chars,
            'maxCharsPerFile': max_chars_per_file
        }
        return processed
    return result

def main():
    parser = DocdbArgumentParser(description="批量获取文件内容", hint="""batch-get-content.py 必须提供 files_json。
示例: openapi_skill_exec skillCode=cms-docdb toolName=batch-get-content argv=["[{\"fileId\":123}]"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("files_json", type=str, help='文件列表 JSON，如 [{"fileId":123},{"fileId":456}]')
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="内容字段总字符上限，<=0 表示不限制")
    parser.add_argument("--max-chars-per-file", type=int, default=DEFAULT_MAX_CHARS_PER_FILE, help="单个内容字段字符上限，<=0 表示不限制")
    args = parser.parse_args()

    files = json.loads(args.files_json)
    result = call_api(files)

    processed_result = process_result(result, args.max_chars, args.max_chars_per_file)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
