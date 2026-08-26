#!/usr/bin/env python3
"""
upload / register-slice 脚本

用途：在分片物理上传到 MinIO 完成后，在服务端注册分片元信息，换取 sliceId

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

# 接口完整 URL（与 openapi/upload/register-slice.md 中声明的一致）
API_PATH = "/document-database/file/uploadFileSliceV2"


def call_api(file_path: str, md5: str, size: int, storage_type: str) -> dict:
    """调用注册分片接口，返回原始 JSON 响应"""
    
    body = {
        "filePath": file_path,
        "md5": md5,
        "size": size,
        "storageType": storage_type
    }

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
    parser = DocdbArgumentParser(description="注册文件分片",
        hint="""register-slice.py 必须提供 file_path md5 size storage_type；真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=register-slice argv=["/tmp/a.bin", "md5hex", "1024", "MINIO", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("file_path", type=str, nargs='?', help="文件完整路径（位置参数）")
    parser.add_argument("md5", type=str, nargs='?', help="文件 MD5（位置参数）")
    parser.add_argument("size", type=int, nargs='?', help="文件大小（位置参数）")
    parser.add_argument("storage_type", type=str, nargs='?', help="存储类型（位置参数）")
    parser.add_argument("--file-path", type=str, dest="file_path_opt", help="文件完整路径（命名参数）")
    parser.add_argument("--md5", type=str, dest="md5_opt", help="文件 MD5（命名参数）")
    parser.add_argument("--size", type=int, dest="size_opt", help="文件大小（命名参数）")
    parser.add_argument("--storage-type", type=str, dest="storage_type_opt", help="存储类型（命名参数）")
    add_safety_args(parser)
    args = parser.parse_args()
    
    file_path = args.file_path or args.file_path_opt
    md5 = args.md5 or args.md5_opt
    size = args.size or args.size_opt
    storage_type = args.storage_type or args.storage_type_opt
    
    if None in [file_path, md5, size, storage_type]:
        print(
            "错误: 缺少参数。用法 argv: [<full_path>, <md5>, <size>, <storage_type>]；"
            "openapi_skill_exec skillCode=cms-docdb toolName=register-slice",
            file=sys.stderr,
        )
        sys.exit(1)

    body = {
        "filePath": file_path,
        "md5": md5,
        "size": size,
        "storageType": storage_type,
    }
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)

    result = call_api(file_path, md5, size, storage_type)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
