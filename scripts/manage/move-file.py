#!/usr/bin/env python3
"""
manage / moveFile — 移动节点（同步 Open API）

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
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

API_PATH = "/document-database/file/moveFile"




def post_json(body: dict) -> dict:
    return request_open_api(API_PATH, method="POST", body=body)

def main():
    parser = DocdbArgumentParser(description="移动文件或文件夹", hint="""move-file.py 必须提供 file_id，且必须带 --target-parent-id。
真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=move-file argv=["12345", "--target-parent-id", "0", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
    parser.add_argument("file_id", type=int, help="被移动节点 ID")
    parser.add_argument("--target-parent-id", type=int, required=True, help="目标父目录 ID")
    parser.add_argument("--new-name", type=str, help="移动后名称，省略则保留原名")
    parser.add_argument("--project-id", type=int, help="目标空间 ID")
    parser.add_argument("--name-conflict-strategy", type=int, default=2,
                        help="0=重命名，1=覆盖，2=失败（默认），3=跳过")
    parser.add_argument("--root-file-id", type=int, help="映射根，用于返回 relativePath")
    add_safety_args(parser)
    args = parser.parse_args()

    body = {
        "fileId": args.file_id,
        "targetParentId": args.target_parent_id,
        "nameConflictStrategy": args.name_conflict_strategy,
    }
    if args.new_name:
        body["newName"] = args.new_name
    if args.project_id is not None:
        body["projectId"] = args.project_id
    if args.root_file_id is not None:
        body["rootFileId"] = args.root_file_id

    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = post_json(body)
    print(json.dumps({
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": result.get("data"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
