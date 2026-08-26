#!/usr/bin/env python3
"""
browse / getMyUploadRecords 脚本

用途：分页查询当前用户在全空间的上传/新建记录（固定操作类型，默认近 90 天）

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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/operationLog/getMyUploadRecords"


def call_api(page_index=None, page_size=None, project_id=None, start_time=None, end_time=None) -> dict:
    params = []
    if page_index is not None:
        params.append(("pageIndex", str(page_index)))
    if page_size is not None:
        params.append(("pageSize", str(page_size)))
    if project_id is not None:
        params.append(("projectId", str(project_id)))
    if start_time is not None:
        params.append(("startTime", str(start_time)))
    if end_time is not None:
        params.append(("endTime", str(end_time)))

    url = API_PATH
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    return request_open_api(url, method="GET")

def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result

def main():
    import argparse

    parser = DocdbArgumentParser(description="分页查询当前用户全空间上传记录（默认近90天）",
        hint="""get-my-upload-records.py get-my-upload-records 按业务参数调用（无必填时可传空 argv）。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-my-upload-records argv=["--page-index", "1"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("--page-index", type=int, help="页码，从1开始")
    parser.add_argument("--page-size", type=int, help="每页条数，最大100")
    parser.add_argument("--project-id", type=int, help="限定某一空间")
    parser.add_argument("--start-time", type=int, help="开始时间戳（毫秒）")
    parser.add_argument("--end-time", type=int, help="结束时间戳（毫秒）")
    args = parser.parse_args()

    result = call_api(
        page_index=args.page_index,
        page_size=args.page_size,
        project_id=args.project_id,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    print(json.dumps(process_result(result), ensure_ascii=False))

if __name__ == "__main__":
    main()
