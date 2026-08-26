#!/usr/bin/env python3
"""
browse / getLevel1Folders 脚本

用途：拉取指定项目空间的根目录下的所有文件夹及文件

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

# 接口完整 URL（与 openapi/browse/get-level1-folders.md 中声明的一致）
API_PATH = "/document-database/file/getLevel1Folders"


def call_api(project_id: int, order: int = None, permission_query: str = None) -> dict:
    """调用获取一级目录接口，返回原始 JSON 响应"""
    
    params = [("projectId", str(project_id))]
    if order is not None:
        params.append(("order", str(order)))
    if permission_query:
        params.append(("permissionQuery", permission_query))

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
    parser = DocdbArgumentParser(description="获取项目空间一级文件夹", hint="""get-level1-folders.py 必须提供 project_id。
个人库根：先 get-personal-project-id.py 取得 projectId，再对本脚本传入该 ID。
示例: python3 -B <skill-dir>/scripts/browse/get-level1-folders.py 10001；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("project_id", type=int, help="项目/空间 ID")
    parser.add_argument("--order", type=int, choices=[1, 2, 5, 6], help="排序规则：1 更新倒序，2 更新顺序，5 名字倒序，6 名字顺序")
    parser.add_argument("--permission-query", type=str, help="权限查询条件")
    args = parser.parse_args()

    result = call_api(
        project_id=args.project_id,
        order=args.order,
        permission_query=args.permission_query
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
