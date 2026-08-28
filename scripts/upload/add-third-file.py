#!/usr/bin/env python3
"""个人知识库：添加第三方虚拟文件（慧记/汇报等）。"""

import json
import os
import sys

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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/project/personal/addThirdFile"
SUPPORTED = {"work_report", "work_plan", "huiji", "ai-report", "url", "notex_result"}


def normalize(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def validate(file_type, relation_id, relation_url):
    if file_type not in SUPPORTED:
        raise SystemExit(f"不支持的虚拟文件类型: {file_type}（禁止 document-database）")
    if not relation_id and not relation_url:
        raise SystemExit("必须提供 --relation-id 或 --relation-url")
    if file_type == "url" and not relation_url:
        raise SystemExit("url 类型必须提供 --relation-url")
    if file_type != "url" and not relation_id:
        raise SystemExit(f"{file_type} 类型必须提供 --relation-id")
    if relation_id and len(relation_id) > 50:
        raise SystemExit("relationId 长度不能超过50")


def main():
    parser = DocdbArgumentParser(
        description="个人知识库挂第三方虚拟文件",
        hint="""add-third-file.py 必须 --project-id、--file-type，以及来源 ID/URL。
示例: python3 -B <skill-dir>/scripts/upload/add-third-file.py --project-id 10001 --file-type huiji --relation-id 1 --relation-title "纪要" --confirm YES
""",
    )
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--file-type", required=True)
    parser.add_argument("--relation-id", default=None)
    parser.add_argument("--relation-url", default=None)
    parser.add_argument("--relation-title", default=None)
    parser.add_argument("--parent-file-id", type=int, default=None)
    parser.add_argument("--folder-path", default=None)
    add_safety_args(parser)
    args = parser.parse_args()

    relation_id = normalize(args.relation_id)
    relation_url = normalize(args.relation_url)
    relation_title = normalize(args.relation_title)
    validate(args.file_type, relation_id, relation_url)

    body = {
        "projectId": args.project_id,
        "fileType": args.file_type,
        "relation": {
            "relationId": relation_id,
            "relationUrl": relation_url,
            "relationTitle": relation_title,
        },
    }
    if args.parent_file_id is not None:
        body["parentFileId"] = args.parent_file_id
    if args.folder_path:
        body["folderPath"] = args.folder_path

    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps({
        "resultCode": result.get("resultCode") if isinstance(result, dict) else None,
        "resultMsg": result.get("resultMsg") if isinstance(result, dict) else None,
        "data": result.get("data") if isinstance(result, dict) else result,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
