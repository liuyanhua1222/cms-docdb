#!/usr/bin/env python3
"""GET /document-database/file/resolvePath — 按相对路径精确解析 fileId

相对 rootFileId（默认 0=空间根）分段精确匹配，非模糊。
成功输出四元组：projectName / projectId / path / fileId；exists=false 时非 0 退出。
"""
import json
import os
import sys
import urllib.parse

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

API_PATH = "/document-database/file/resolvePath"
PROJECT_LIST_PATH = "/document-database/project/list"


def normalize_relative_path(path: str) -> str:
    """与 folder-navigator 对齐：反斜杠→/，去首尾空白与 /。"""
    return (path or "").replace("\\", "/").strip().strip("/")


def _lookup_project_name(project_id: int, app_code: str = None) -> str:
    """Best-effort：从 project/list 取空间名；失败返回空串。"""
    params = []
    if app_code:
        params.append(("appCode", app_code))
    url = PROJECT_LIST_PATH
    if params:
        url = f"{PROJECT_LIST_PATH}?{urllib.parse.urlencode(params)}"
    try:
        result = request_open_api(url, method="GET")
    except Exception as ex:
        print(f"警告: 查询空间名失败 — {ex}", file=sys.stderr)
        return ""
    if not isinstance(result, dict) or result.get("resultCode") != 1:
        print("警告: 查询空间名失败（project/list）", file=sys.stderr)
        return ""
    data = result.get("data") or []
    if not isinstance(data, list):
        return ""
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("id") == project_id or str(item.get("id")) == str(project_id):
            return item.get("name") or item.get("projectName") or ""
    return ""


def resolve_path(project_id: int, path: str, root_file_id: int = 0) -> dict:
    params = [
        ("projectId", str(project_id)),
        ("rootFileId", str(root_file_id)),
        ("path", path),
    ]
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"
    return request_open_api(url, method="GET")


def main():
    p = DocdbArgumentParser(
        hint="""resolve-path.py 必须提供 --project-id 与 --path。
相对空间根（--root-file-id 默认 0）精确解析；多级路径用 / 分隔。
示例: python3 -B <skill-dir>/scripts/browse/resolve-path.py --project-id 2096847627596439554 --path "集团/产品中心/20260907_产品中心BP研讨归档_V1.0"
""",
    )
    p.add_argument("--project-id", type=int, required=True, help="空间 projectId（必填，避免跨空间误解析）")
    p.add_argument("--path", type=str, required=True, help="相对 rootFileId 的路径（支持多级）")
    p.add_argument("--root-file-id", type=int, default=0, help="映射根 fileId，默认 0=空间根")
    p.add_argument("--app-code", type=str, default="", help="可选：查空间名时传入 appCode")
    args = p.parse_args()

    path = normalize_relative_path(args.path)
    if not path:
        print(
            json.dumps(
                {"resultCode": -1, "resultMsg": "path 不能为空", "data": {}},
                ensure_ascii=False,
            )
        )
        sys.exit(2)

    try:
        raw = resolve_path(args.project_id, path, args.root_file_id)
    except Exception as ex:
        print(
            json.dumps(
                {"resultCode": -1, "resultMsg": f"resolvePath 调用失败: {ex}", "data": {}},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    if not isinstance(raw, dict) or raw.get("resultCode") != 1:
        msg = raw.get("resultMsg") if isinstance(raw, dict) else str(raw)
        print(
            json.dumps(
                {"resultCode": -1, "resultMsg": f"resolvePath 业务失败: {msg}", "data": raw},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    data = raw.get("data") or {}
    exists = bool(data.get("exists"))
    file_id = data.get("fileId")
    file_type = data.get("type")
    project_name = _lookup_project_name(args.project_id, args.app_code or None)

    out_data = {
        "exists": exists,
        "projectName": project_name,
        "projectId": args.project_id,
        "path": path,
        "fileId": file_id,
        "type": file_type,
        "rootFileId": args.root_file_id,
    }
    if not project_name:
        out_data["projectNameWarning"] = "未能解析空间名；请核对 projectId / --app-code"

    if not exists or file_id is None:
        print(
            json.dumps(
                {
                    "resultCode": -1,
                    "resultMsg": f"路径不存在或不完整: projectId={args.project_id} path={path}",
                    "data": out_data,
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    print(
        json.dumps(
            {
                "resultCode": 1,
                "resultMsg": None,
                "data": out_data,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
