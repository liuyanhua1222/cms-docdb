#!/usr/bin/env python3
"""
query / batchGetMeta 脚本

用途：按 fileId 批量查元数据（无正文），用于对账

使用方式：
  python3 -B <skill-dir>/scripts/query/batch-get-meta.py --file-ids 123,456
  python3 -B <skill-dir>/scripts/query/batch-get-meta.py --files-json '[123,456]'

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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/file/batchGetMeta"


def parse_file_ids(file_ids: str = None, files_json: str = None) -> list:
    if file_ids and files_json:
        print("错误: --file-ids 与 --files-json 只能二选一", file=sys.stderr)
        sys.exit(2)
    if not file_ids and not files_json:
        print("错误: 必须提供 --file-ids 或 --files-json", file=sys.stderr)
        sys.exit(2)

    if file_ids:
        parts = [p.strip() for p in file_ids.split(",") if p.strip()]
        if not parts:
            print("错误: --file-ids 为空", file=sys.stderr)
            sys.exit(2)
        try:
            return [int(p) for p in parts]
        except ValueError:
            print("错误: --file-ids 须为逗号分隔的整数", file=sys.stderr)
            sys.exit(2)

    raw = json.loads(files_json)
    if isinstance(raw, dict) and "fileIds" in raw:
        raw = raw["fileIds"]
    if not isinstance(raw, list) or not raw:
        print("错误: --files-json 须为非空 fileId 数组，或 {\"fileIds\":[...]}", file=sys.stderr)
        sys.exit(2)
    out = []
    for item in raw:
        if isinstance(item, dict):
            fid = item.get("fileId") or item.get("id")
            if fid is None:
                print("错误: files-json 对象项缺少 fileId", file=sys.stderr)
                sys.exit(2)
            out.append(int(fid))
        else:
            out.append(int(item))
    return out


def call_api(file_ids: list) -> dict:
    return request_open_api(API_PATH, method="POST", body={"fileIds": file_ids})


def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result


def main():
    parser = DocdbArgumentParser(
        description="按 fileId 批量查元数据（无正文）",
        hint="""batch-get-meta.py 必须提供 --file-ids（逗号分隔）或 --files-json。
示例: python3 -B <skill-dir>/scripts/query/batch-get-meta.py --file-ids 123,456
示例: python3 -B <skill-dir>/scripts/query/batch-get-meta.py --files-json '[123,456]'
""",
    )
    parser.add_argument("--file-ids", dest="file_ids", type=str, default=None, help="逗号分隔 fileId，如 123,456")
    parser.add_argument(
        "--files-json",
        dest="files_json",
        type=str,
        default=None,
        help='JSON：fileId 数组，或 [{"fileId":123}]，或 {"fileIds":[123]}',
    )
    args = parser.parse_args()

    ids = parse_file_ids(args.file_ids, args.files_json)
    result = call_api(ids)
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
