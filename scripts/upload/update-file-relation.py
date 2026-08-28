#!/usr/bin/env python3
"""共享空间：单条第三方虚拟文件新增/更新（Open API 固定 operationType=1）。"""

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

API_PATH = "/document-database/relation/updateFileRelation"
SUPPORTED = {"work_report", "work_plan", "huiji", "ai-report", "url", "notex_result"}


def normalize(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def validate(file_type, relation_id, relation_url, relation_title):
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
    if not relation_title:
        raise SystemExit(
            "必须提供 --relation-title（与 PC 一致：huiji/notex→name，ai-report→taskName，"
            "work_report/work_plan→main，url→链接名）"
        )


def main():
    parser = DocdbArgumentParser(
        description="共享空间单条虚拟文件归档",
        hint="""update-file-relation.py 必须 --file-type、来源字段与 --relation-title（第三方原标题，对齐 PC）。
脚本固定发送 operationType=1。同目录同来源幂等。
""",
    )
    parser.add_argument("--file-type", required=True)
    parser.add_argument("--relation-id", default=None)
    parser.add_argument("--relation-url", default=None)
    parser.add_argument("--relation-title", required=True,
                        help="第三方原标题（必填，对齐 PC：name/taskName/main/链接名）")
    parser.add_argument("--project-id", type=int, default=None)
    parser.add_argument("--parent-file-id", type=int, default=None)
    parser.add_argument("--folder-path", default=None)
    parser.add_argument("--file-id", type=int, default=None)
    add_safety_args(parser)
    args = parser.parse_args()

    relation_id = normalize(args.relation_id)
    relation_url = normalize(args.relation_url)
    relation_title = normalize(args.relation_title)
    validate(args.file_type, relation_id, relation_url, relation_title)

    can_resolve = (
        args.parent_file_id is not None
        and args.parent_file_id > 0
        and not args.folder_path
    )
    if args.file_id is None and args.project_id is None and not can_resolve:
        raise SystemExit("新增时必须提供 --project-id，或有效的 --parent-file-id（且不用 --folder-path）")

    body = {
        "fileType": args.file_type,
        "relationId": relation_id,
        "relationUrl": relation_url,
        "relationTitle": relation_title,
        "operationType": 1,
    }
    if args.project_id is not None:
        body["projectId"] = args.project_id
    if args.parent_file_id is not None:
        body["parentFileId"] = args.parent_file_id
    if args.folder_path:
        body["folderPath"] = args.folder_path
    if args.file_id is not None:
        body["fileId"] = args.file_id

    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps({
        "resultCode": result.get("resultCode") if isinstance(result, dict) else None,
        "resultMsg": result.get("resultMsg") if isinstance(result, dict) else None,
        "data": result.get("data") if isinstance(result, dict) else result,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
