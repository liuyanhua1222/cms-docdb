#!/usr/bin/env python3
"""
browse / getPersonalProjectId 脚本

用途：获取当前用户的个人知识库空间 ID

使用方式：

说明：
  --app-code 为产品通道；不传则由后端按企业默认解析（勿理解为固定默认 kz_doc）。

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

# 接口完整 URL（与 openapi/browse/get-personal-project-id.md 中声明的一致）
API_PATH = "/document-database/project/personal/getProjectId"


def call_api(app_code: str = None) -> dict:
    """调用获取个人空间 ID 接口，返回原始 JSON 响应"""
    
    params = []
    if app_code:
        params.append(("appCode", app_code))

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
    import argparse
    parser = DocdbArgumentParser(description="获取当前用户的个人知识库空间 ID",
        hint="""get-personal-project-id.py get-personal-project-id 按业务参数调用（无必填时可传空 argv）。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-personal-project-id argv=[]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument(
        "--app-code",
        type=str,
        help="应用通道编码：kz_doc / fw_doc / kz_knowledge_base（不传=后端按企业默认）",
    )
    args = parser.parse_args()

    result = call_api(app_code=args.app_code)

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
