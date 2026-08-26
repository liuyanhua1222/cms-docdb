#!/usr/bin/env python3
"""
query / search 脚本

用途：根据关键词搜索文件或目录

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

# 接口完整 URL（与 openapi/query/search.md 中声明的一致）
API_PATH = "/document-database/file/searchFile"


def call_api(name_key: str, project_id: int = None, root_file_id: int = None,
             start_time: int = None, end_time: int = None,
             is_file_storage: bool = None, permission_query: str = None,
             exclude_file_types: str = None, exclude_folder_names: str = None) -> dict:
    """调用文件搜索接口，返回原始 JSON 响应"""
    
    # nameKey 必须 URL 编码
    params = [("nameKey", name_key)]
    if project_id is not None:
        params.append(("projectId", str(project_id)))
    if root_file_id is not None:
        params.append(("rootFileId", str(root_file_id)))
    if start_time is not None:
        params.append(("startTime", str(start_time)))
    if end_time is not None:
        params.append(("endTime", str(end_time)))
    if is_file_storage is not None:
        params.append(("isFileStorage", "true" if is_file_storage else "false"))
    if permission_query:
        params.append(("permissionQuery", permission_query))
    if exclude_file_types:
        params.append(("excludeFileTypes", exclude_file_types))
    if exclude_folder_names:
        params.append(("excludeFolderNames", exclude_folder_names))

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
    parser = DocdbArgumentParser(description="按关键词搜索文件", hint="""search.py 必须提供 name_key，且必须带 --project-id。
示例: openapi_skill_exec skillCode=cms-docdb toolName=search argv=["合同", "--project-id", "10001"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("name_key", type=str, help="搜索关键词（必填）")
    parser.add_argument("--project-id", type=int, required=True, help="项目/空间 ID（必填，用于限定搜索范围）")
    parser.add_argument("--root-file-id", type=int, help="指定根目录 ID（可选）")
    parser.add_argument("--start-time", type=int, help="开始时间戳（毫秒，可选）")
    parser.add_argument("--end-time", type=int, help="结束时间戳（毫秒，可选）")
    parser.add_argument("--is-file-storage", action="store_true", help="文件存储范围（可选）")
    parser.add_argument("--permission-query", type=str, help="权限查询条件（可选）")
    parser.add_argument("--exclude-file-types", type=str, help="排除的文件类型，逗号分隔（可选）")
    parser.add_argument("--exclude-folder-names", type=str, help="排除的文件夹名称，逗号分隔（可选）")
    args = parser.parse_args()

    result = call_api(
        name_key=args.name_key,
        project_id=args.project_id,
        root_file_id=args.root_file_id,
        start_time=args.start_time,
        end_time=args.end_time,
        is_file_storage=args.is_file_storage,
        permission_query=args.permission_query,
        exclude_file_types=args.exclude_file_types,
        exclude_folder_names=args.exclude_folder_names
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
