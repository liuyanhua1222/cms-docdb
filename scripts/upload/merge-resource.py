#!/usr/bin/env python3
"""
upload / merge-resource 脚本

用途：合并所有已注册的分片，生成最终的 resourceId

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
from safety import add_safety_args, enforce_or_dry_run

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/upload/merge-resource.md 中声明的一致）
API_PATH = "/document-database/file/saveResource"


def call_api(name: str, slice_ids: list, suffix: str = None, size: int = None) -> dict:
    """调用合并分片接口，返回原始 JSON 响应"""
    
    body = {
        "name": name,
        "sliceIds": slice_ids
    }
    if suffix:
        body["suffix"] = suffix
    if size is not None:
        body["size"] = size

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
    parser = DocdbArgumentParser(description="合并分片生成最终 resourceId",
        hint="""merge-resource.py 必须提供 name 与 slice_ids；真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=merge-resource argv=["报告.pdf", "slice1,slice2", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("name", type=str, help="文件名（含后缀）")
    parser.add_argument("slice_ids", type=str, help="分片 ID 列表，逗号分隔")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件总大小（字节）")
    add_safety_args(parser)
    args = parser.parse_args()

    slice_ids = [int(x.strip()) for x in args.slice_ids.split(",")]
    body = {"name": args.name, "sliceIds": slice_ids}
    if args.suffix:
        body["suffix"] = args.suffix
    if args.size is not None:
        body["size"] = args.size
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)

    result = call_api(name=args.name, slice_ids=slice_ids, suffix=args.suffix, size=args.size)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
