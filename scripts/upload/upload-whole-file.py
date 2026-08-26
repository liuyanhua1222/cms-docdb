#!/usr/bin/env python3
"""
upload / upload-whole-file 脚本

用途：上传本地完整文件（建议 20MB 以下），直接返回 resourceId
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
from docdb_open_api import ensure_common_on_path, upload_multipart_file
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/cwork-file/uploadWholeFile"


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

    parser = DocdbArgumentParser(description="上传完整文件到知识库",
        hint="""upload-whole-file.py 必须提供 file_path；真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=upload-whole-file argv=["/tmp/a.pdf", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("file_path", type=str, nargs="?", help="文件路径（位置参数）")
    parser.add_argument("--file-path", type=str, dest="file_path_opt", help="文件路径（命名参数）")
    add_safety_args(parser)
    args = parser.parse_args()

    file_path = args.file_path or args.file_path_opt
    if file_path is None:
        print("错误: 请提供文件路径", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(file_path):
        print(f"错误: 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    enforce_or_dry_run(
        args,
        method="POST",
        url=API_PATH,
        body={"filePath": file_path, "fileName": os.path.basename(file_path)},
    )

    result = upload_multipart_file(API_PATH, file_path)
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
