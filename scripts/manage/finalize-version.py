#!/usr/bin/env python3
"""
manage / finalizeVersion 脚本

用途：将文件的某个版本标记为正式定稿状态（status 从 1 变为 2）。
      不传 version_number 则定稿最新版本。

使用方式：
  # 定稿最新版本

  # 定稿指定版本号

"""

import sys
import os
import json
import time

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

API_PATH = "/document-database/file/finalizeVersion"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_INTERVAL = 1


def call_api(payload: dict) -> dict:
    return request_open_api(url if "url" in dir() else API_PATH, method="GET")
def main() -> None:
    parser = DocdbArgumentParser(description="版本定稿", hint="""finalize-version.py 必须提供 file_id。
真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=finalize-version argv=["12345", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--version-number", type=int, default=0,
                        help="要定稿的版本号（不传或传 0 则定稿最新版本）")
    add_safety_args(parser)
    args = parser.parse_args()

    payload = {"fileId": args.file_id}
    if args.version_number:
        payload["versionNumber"] = args.version_number

    enforce_or_dry_run(args, method="POST", url=API_PATH, body=payload)
    result = call_api(payload)
    output = {
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": result.get("data"),
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
