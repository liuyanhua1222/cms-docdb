#!/usr/bin/env python3
"""
query / listDescendantFiles 脚本

用途：在 rootFileId 下分页扁平列举后代文件（冷启动同步）

使用方式：
  python3 -B <skill-dir>/scripts/query/list-descendant-files.py --root-file-id 10086 --project-id 2025001

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

API_PATH = "/document-database/file/listDescendantFiles"


def call_api(
    root_file_id: int,
    project_id: int = None,
    suffix: str = "md",
    cursor: str = None,
    limit: int = None,
    include_path: bool = False,
    include_folders: bool = False,
) -> dict:
    params = [("rootFileId", str(root_file_id))]
    if project_id is not None:
        params.append(("projectId", str(project_id)))
    if suffix is not None:
        params.append(("suffix", suffix))
    if cursor:
        params.append(("cursor", cursor))
    if limit is not None:
        params.append(("limit", str(limit)))
    if include_path:
        params.append(("includePath", "true"))
    if include_folders:
        params.append(("includeFolders", "true"))
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"
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
    parser = DocdbArgumentParser(
        description="子树扁平列举（后代文件元数据）",
        hint="""list-descendant-files.py 必须提供 --root-file-id（可为 0 表示空间根）。
示例: python3 -B <skill-dir>/scripts/query/list-descendant-files.py --root-file-id 10086 --project-id 2025001 --include-path
""",
    )
    parser.add_argument("--root-file-id", dest="root_file_id", required=True, type=int, help="映射根目录 fileId（必填；0=空间根）")
    parser.add_argument("--project-id", type=int, default=None, help="项目/空间 ID（可选）")
    parser.add_argument("--suffix", type=str, default="md", help="后缀过滤，默认 md")
    parser.add_argument("--cursor", type=str, default=None, help="分页游标")
    parser.add_argument("--limit", type=int, default=None, help="每页条数")
    parser.add_argument("--include-path", action="store_true", help="返回 relativePath")
    parser.add_argument("--include-folders", action="store_true", help="一并返回文件夹")
    args = parser.parse_args()

    result = call_api(
        root_file_id=args.root_file_id,
        project_id=args.project_id,
        suffix=args.suffix,
        cursor=args.cursor,
        limit=args.limit,
        include_path=args.include_path,
        include_folders=args.include_folders,
    )
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
