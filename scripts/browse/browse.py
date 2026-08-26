#!/usr/bin/env python3
"""
browse / browse 脚本

用途：浏览指定目录下的直接子项（文件和文件夹）

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

# 接口完整 URL（与 openapi/browse/browse.md 中声明的一致）
API_PATH = "/document-database/file/getChildFiles"


def call_api(parent_id: int, type: int = None, order: int = None,
             exclude_file_types: str = None, exclude_folder_names: str = None,
             return_file_desc: bool = True) -> dict:
    """调用浏览目录接口，返回原始 JSON 响应"""
    
    params = [("parentId", str(parent_id))]
    if type is not None:
        params.append(("type", str(type)))
    if order is not None:
        params.append(("order", str(order)))
    if exclude_file_types:
        params.append(("excludeFileTypes", exclude_file_types))
    if exclude_folder_names:
        params.append(("excludeFolderNames", exclude_folder_names))
    if return_file_desc:
        params.append(("returnFileDesc", "true"))

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
        description="浏览目录下的文件和文件夹",
        hint="""browse.py 必须提供 parent_id：
- 个人库根目录传 0
- 项目空间请传该空间 rootFileId（勿对任意空间一律传 0）
示例: openapi_skill_exec skillCode=cms-docdb toolName=browse argv=["0"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
"""
    )
    parser.add_argument(
        "parent_id",
        type=int,
        help="父目录 ID：个人库根传 0；项目空间传该空间 rootFileId",
    )
    parser.add_argument("--type", type=int, choices=[1, 2], help="1 只查文件夹，2 只查文件")
    parser.add_argument("--order", type=int, choices=[1, 2, 3, 4, 5, 6], help="排序规则")
    parser.add_argument("--exclude-file-types", type=str, help="排除的文件类型，逗号分隔")
    parser.add_argument("--exclude-folder-names", type=str, help="排除的文件夹名称，逗号分隔")
    parser.add_argument("--no-return-file-desc", action="store_true", help="不返回文件描述")
    args = parser.parse_args()

    result = call_api(
        parent_id=args.parent_id,
        type=args.type,
        order=args.order,
        exclude_file_types=args.exclude_file_types,
        exclude_folder_names=args.exclude_folder_names,
        return_file_desc=not args.no_return_file_desc
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
