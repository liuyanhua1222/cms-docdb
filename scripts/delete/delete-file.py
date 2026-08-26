#!/usr/bin/env python3
"""
delete / deleteFile 脚本

用途：删除指定文件（支持逻辑删除或物理彻底删除）

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

# 接口完整 URL（与 openapi/delete/delete-file.md 中声明的一致）
API_PATH = "/document-database/file/deleteFile"


def call_api(file_id: int, is_physical: bool = False) -> dict:
    """调用删除文件接口，返回原始 JSON 响应"""
    
    body = {"fileId": file_id}
    if is_physical:
        body["isPhysical"] = True

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
    parser = DocdbArgumentParser(description="删除文件", hint="""delete-file.py 必须提供 file_id。
真实删除还需 --confirm YES（物理删除用 --physical 且 --confirm PHYSICAL）。
示例: openapi_skill_exec skillCode=cms-docdb toolName=delete-file argv=["12345", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("file_id", type=int, help="要删除的文件 ID")
    parser.add_argument("--physical", action="store_true", help="加上此参数则物理彻底删除，否则移入回收站")
    add_safety_args(parser)
    args = parser.parse_args()

    body = {"fileId": args.file_id}
    if args.physical:
        body["isPhysical"] = True
    enforce_or_dry_run(
        args,
        method="POST",
        url=API_PATH,
        body=body,
        require_physical_confirm=bool(args.physical),
    )

    result = call_api(file_id=args.file_id, is_physical=args.physical)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
