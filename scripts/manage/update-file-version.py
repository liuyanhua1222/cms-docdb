#!/usr/bin/env python3
"""
manage / updateFileVersion 脚本

用途：将已上传的物理文件资源绑定到已有文件，按 versionStatus 更新或定稿版本
      （不一定总是插入新版本行；见下方说明）。

使用方式（面向 AI：全带名）：
  python3 -B .../update-file-version.py --file-id <fid> --resource-id <rid> [--project-id <pid>] \\
    [--version-status 3] [--version-name "V2.0"] [--version-remark "修订内容"] \\
    [--suffix pdf] [--size 204800] --confirm YES

versionStatus 说明（本脚本默认 3）：
  1 = 上一版为草稿则覆盖；已定稿则新建草稿
  2 = 强制新建未定稿版本（若需再定稿，另调 finalize-version.py）
  3 = 本脚本默认。上一版已定稿/无历史：插入新行并定稿（涨号）；
      上一版仍是草稿：原地覆盖并定稿（版本号不变，不会多一条历史）

若必须「历史多一条再定稿」：传 --version-status 2，再调 finalize-version.py。
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

API_PATH = "/document-database/file/updateFileVersion"


def call_api(payload: dict) -> dict:
    return request_open_api(API_PATH, method="POST", body=payload)


def main() -> None:
    parser = DocdbArgumentParser(
        description="用新资源更新文件版本",
        hint="""update-file-version.py 必须提供 --file-id 与 --resource-id。
--project-id 可选（省略则由 OpenAPI 从文件反查）。真实写入还需 --confirm YES。
默认 --version-status 3（草稿上可能原地定稿、版本号不变）。
示例: python3 -B <skill-dir>/scripts/manage/update-file-version.py --file-id 12345 --resource-id 999 --confirm YES；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("--file-id", type=int, required=True, help="要更新的文件 ID")
    parser.add_argument(
        "--resource-id",
        type=int,
        required=True,
        help="新上传的物理资源 ID（必填）",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        help="文件所在空间 ID（可选；省略则由 OpenAPI 从 fileId 反查）",
    )
    parser.add_argument("--name", type=str, help="文件名（可选，不传则保持原文件名）")
    parser.add_argument(
        "--version-status",
        type=int,
        default=3,
        help=(
            "版本行为（默认 3）：1=草稿覆盖/已定稿则新建草稿；"
            "2=强制新建未定稿；"
            "3=已定稿则新行并定稿，草稿则原地覆盖并定稿（版本号可能不变）"
        ),
    )
    parser.add_argument("--version-name", type=str, help="版本名称，如 V2.0")
    parser.add_argument("--version-remark", type=str, help="版本说明")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件大小（字节）")
    add_safety_args(parser)
    args = parser.parse_args()

    payload = {
        "id": args.file_id,
        "resourceId": args.resource_id,
        "versionStatus": args.version_status,
    }
    if args.project_id is not None:
        payload["projectId"] = args.project_id
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
