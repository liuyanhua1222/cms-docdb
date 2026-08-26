#!/usr/bin/env python3
"""
manage / updateFileVersion 脚本

用途：将已上传的物理文件资源绑定到已有文件，产生新版本记录。

使用方式：
    [--version-status 3] [--version-name "V2.0"] [--version-remark "修订内容"] \
    [--suffix pdf] [--size 204800]

versionStatus 说明：
  1 = 覆盖当前草稿（默认）
  2 = 强制新建版本
  3 = 新建版本并立即定稿（推荐）

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

API_PATH = "/document-database/file/updateFileVersion"
TIMEOUT = 60
MAX_RETRIES = 3
RETRY_INTERVAL = 1


def call_api(payload: dict) -> dict:
    return request_open_api(API_PATH, method="POST", body=payload)


def main() -> None:
    parser = DocdbArgumentParser(description="用新资源更新文件版本", hint="""update-file-version.py 必须提供 file_id project_id resource_id。
真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/manage/update-file-version.py 12345 10001 999 --confirm YES；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("file_id", type=int, help="要更新的文件 ID")
    parser.add_argument("project_id", type=int, help="文件所在空间 ID")
    parser.add_argument("resource_id", type=int, help="新上传的物理资源 ID")
    parser.add_argument("--name", type=str, help="文件名（可选，不传则保持原文件名）")
    parser.add_argument("--version-status", type=int, default=3,
                        help="版本行为：1=覆盖草稿，2=强制新建，3=新建并立即定稿（默认 3）")
    parser.add_argument("--version-name", type=str, help="版本名称，如 V2.0")
    parser.add_argument("--version-remark", type=str, help="版本说明")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件大小（字节）")
    add_safety_args(parser)
    args = parser.parse_args()

    payload = {
        "id": args.file_id,
        "projectId": args.project_id,
        "resourceId": args.resource_id,
        "versionStatus": args.version_status,
    }
    if args.name:
        payload["name"] = args.name
    if args.version_name:
        payload["versionName"] = args.version_name
    if args.version_remark:
        payload["versionRemark"] = args.version_remark
    if args.suffix:
        payload["suffix"] = args.suffix
    if args.size:
        payload["size"] = args.size

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
