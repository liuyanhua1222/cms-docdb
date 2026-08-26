#!/usr/bin/env python3
"""
browse / listAllApps 脚本

用途：获取当前企业下用户可访问的知识库应用（产品通道）列表。
用于意图不明时先按企业收敛选项，再决定 project/list 的 appCode。

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

if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


API_PATH = "/document-database/app/listAll"




def call_api() -> dict:
    return request_open_api(API_PATH, method="GET")


def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result


def main():
    parser = DocdbArgumentParser(description="获取当前企业可用知识库应用通道",
        hint="""get-app-list.py get-app-list 按业务参数调用（无必填时可传空 argv）。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-app-list argv=[]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.parse_args()
    result = call_api()
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
