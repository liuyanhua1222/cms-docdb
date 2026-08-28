#!/usr/bin/env python3
"""共享空间：批量添加第三方虚拟文件（逐条目录级幂等）。"""

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

API_PATH = "/document-database/relation/batchAddFileRelation"
SUPPORTED = {"work_report", "work_plan", "huiji", "ai-report", "url", "notex_result"}


def normalize(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def validate_one(file_type, relation_id, relation_url):
    if not relation_id and not relation_url:
        raise SystemExit("每条 relations 必须提供 relationId 或 relationUrl")
    if file_type == "url" and not relation_url:
        raise SystemExit("url 类型每条必须提供 relationUrl")
    if file_type != "url" and not relation_id:
        raise SystemExit(f"{file_type} 类型每条必须提供 relationId")
    if relation_id and len(relation_id) > 50:
        raise SystemExit("relationId 长度不能超过50")


def main():
    parser = DocdbArgumentParser(
        description="共享空间批量虚拟文件归档",
        hint="""batch-add-file-relation.py 必须 --file-type 与 --relations-json。
relations-json 示例: [{"relationId":"1","relationTitle":"A"}]
""",
    )
    parser.add_argument("--file-type", required=True)
    parser.add_argument("--relations-json", required=True, help="JSON 数组")
    parser.add_argument("--project-id", type=int, default=None)
    parser.add_argument("--parent-file-id", type=int, default=None)
    parser.add_argument("--folder-path", default=None)
    add_safety_args(parser)
    args = parser.parse_args()

    if args.file_type not in SUPPORTED:
        raise SystemExit(f"不支持的虚拟文件类型: {args.file_type}（禁止 document-database）")

    try:
        raw_relations = json.loads(args.relations_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"relations-json 不是合法 JSON: {exc}") from exc
    if not isinstance(raw_relations, list) or not raw_relations:
        raise SystemExit("relations-json 必须是非空数组")

    relations = []
    for item in raw_relations:
        if not isinstance(item, dict):
            raise SystemExit("relations-json 每个元素必须是对象")
        relation_id = normalize(item.get("relationId") or item.get("relation_id"))
        relation_url = normalize(item.get("relationUrl") or item.get("relation_url"))
        relation_title = normalize(item.get("relationTitle") or item.get("relation_title"))
        validate_one(args.file_type, relation_id, relation_url)
        entry = {
            "relationId": relation_id,
            "relationUrl": relation_url,
            "relationTitle": relation_title,
        }
        reporters = item.get("reporterIdList") or item.get("reporter_id_list")
        if reporters:
            entry["reporterIdList"] = reporters
        relations.append(entry)

    can_resolve = (
        args.parent_file_id is not None
        and args.parent_file_id > 0
        and not args.folder_path
    )
    if args.project_id is None and not can_resolve:
        raise SystemExit("必须提供 --project-id，或有效的 --parent-file-id（且不用 --folder-path）")

    body = {
        "fileType": args.file_type,
        "relations": relations,
    }
    if args.project_id is not None:
        body["projectId"] = args.project_id
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
