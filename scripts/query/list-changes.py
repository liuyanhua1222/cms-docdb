#!/usr/bin/env python3
"""
query / listChanges 脚本

用途：按 since/cursor 拉取增量变更（知识库增量同步）

使用方式：
  python3 -B <skill-dir>/scripts/query/list-changes.py --project-id 2025001 --since 1714972800000

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

API_PATH = "/document-database/file/listChanges"


def call_api(
    project_id: int = None,
    root_file_id: int = None,
    since: int = None,
    cursor: str = None,
    limit: int = None,
    include_path: bool = False,
    include_move_hint: bool = False,
) -> dict:
    params = []
    if project_id is not None:
        params.append(("projectId", str(project_id)))
    if root_file_id is not None:
        params.append(("rootFileId", str(root_file_id)))
    if since is not None:
        params.append(("since", str(since)))
    if cursor:
        params.append(("cursor", cursor))
    if limit is not None:
        params.append(("limit", str(limit)))
    if include_path:
        params.append(("includePath", "true"))
    if include_move_hint:
        params.append(("includeMoveHint", "true"))
    url = API_PATH if not params else f"{API_PATH}?{urllib.parse.urlencode(params)}"
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
        description="增量变更列表（since/cursor）",
        hint="""list-changes.py 参数均可选；建议传 --project-id 与 --since（或 --cursor）限定范围。
示例: python3 -B <skill-dir>/scripts/query/list-changes.py --project-id 2025001 --since 1714972800000 --include-path
""",
    )
    parser.add_argument("--project-id", type=int, default=None, help="项目/空间 ID（可选）")
    parser.add_argument("--root-file-id", dest="root_file_id", type=int, default=None, help="限定子树根；0=空间根")
    parser.add_argument("--since", type=int, default=None, help="水位时间戳（毫秒）")
    parser.add_argument("--cursor", type=str, default=None, help="分页游标")
    parser.add_argument("--limit", type=int, default=None, help="每页条数")
    parser.add_argument("--include-path", action="store_true", help="返回 relativePath")
    parser.add_argument("--include-move-hint", action="store_true", help="返回移动提示字段")
    args = parser.parse_args()

    result = call_api(
        project_id=args.project_id,
        root_file_id=args.root_file_id,
        since=args.since,
        cursor=args.cursor,
        limit=args.limit,
        include_path=args.include_path,
        include_move_hint=args.include_move_hint,
    )
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
