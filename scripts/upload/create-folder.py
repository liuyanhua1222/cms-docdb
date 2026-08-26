#!/usr/bin/env python3
"""
upload / createFolder 脚本

用途：在指定空间/父目录下显式创建空文件夹（同步建目录、预置目录结构）

使用方式：

  parentId != 0 时默认通过 getFileBasicInfo 自动解析 projectId。

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
from docdb_open_api import ensure_common_on_path, request_open_api, resolve_project_id_for_parent
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/file/createFolder"


def call_api(project_id: int, parent_id: int, name: str, cover: bool, auto_rename: bool) -> dict:
    body = {
        "projectId": project_id,
        "parentId": parent_id,
        "name": name,
        "cover": cover,
        "autoRename": auto_rename,
    }
    return request_open_api(API_PATH, method="POST", body=body)
def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result

def main():
    parser = DocdbArgumentParser(description="在指定父目录下创建文件夹", hint="""create-folder.py 必须提供 parent_id 与 name。
真实写入还需 --confirm YES（可先 --dry-run）。
示例: python3 -B <skill-dir>/scripts/upload/create-folder.py 0 "新产品" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("parent_id", type=int, help="父目录 fileId，空间根传 0")
    parser.add_argument("name", type=str, help="文件夹名称（勿含 / 或 \）")
    parser.add_argument("--project-id", type=int, default=None, help="空间 ID；parentId!=0 时可省略（自动反查）")
    parser.add_argument("--no-resolve-project-id", action="store_true", help="不调用 getFileBasicInfo（不推荐）")
    parser.add_argument("--cover", action="store_true", help="同名时覆盖（慎用）")
    parser.add_argument("--auto-rename", action="store_true", help="同名时自动重命名")
    add_safety_args(parser)
    args = parser.parse_args()

    body_preview = {
        "projectId": args.project_id,
        "parentId": args.parent_id,
        "name": args.name,
        "cover": args.cover,
        "autoRename": args.auto_rename,
    }
    enforce_or_dry_run(
        args,
        method="POST",
        url=API_PATH,
        body=body_preview,
        extra={"projectIdResolved": False},
    )

    if args.no_resolve_project_id:
        if args.project_id is None:
            print("错误: --no-resolve-project-id 模式下必须提供 --project-id", file=sys.stderr)
            sys.exit(1)
        project_id = args.project_id
    else:
        project_id = resolve_project_id_for_parent(args.parent_id, args.project_id)

    result = call_api(
        project_id=project_id,
        parent_id=args.parent_id,
        name=args.name,
        cover=args.cover,
        auto_rename=args.auto_rename,
    )
    print(json.dumps(process_result(result), ensure_ascii=False))

if __name__ == "__main__":
    main()
