#!/usr/bin/env python3
"""GET /document-database/admin/isProjectMember — 判断当前调用人是否空间成员。

注意：OpenAPI 仅支持「当前调用人」。若需预检被授权人，请传 --employee-id，
脚本会改走 listMembers 并检查目标是否在列表中（须管理员）。
"""
import sys, os, json
import urllib.parse

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

API_PATH = "/document-database/admin/isProjectMember"
LIST_PATH = "/document-database/admin/listMembers"


def main():
    p = DocdbArgumentParser(hint="""is-project-member.py 必须提供 --project-id。
默认检查当前调用人。预检他人请加 --employee-id（走 listMembers）。
示例: python3 -B <skill-dir>/scripts/admin/is-project-member.py --project-id 10001
示例: python3 -B <skill-dir>/scripts/admin/is-project-member.py --project-id 10001 --employee-id 2
""")
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    p.add_argument(
        "--employee-id",
        type=int,
        default=None,
        help="被授权人 employeeId；提供则用 listMembers 预检（需管理员）",
    )
    args = p.parse_args()
    if args.employee_id is None:
        url = f"{API_PATH}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
        result = request_open_api(url, method="GET")
        print(json.dumps(result, ensure_ascii=False))
        return

    url = f"{LIST_PATH}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
    listed = request_open_api(url, method="GET")
    data = listed.get("data") if isinstance(listed, dict) else None
    found = False
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            eid = row.get("employeeId") or row.get("empId") or row.get("id")
            if eid is not None and int(eid) == int(args.employee_id):
                found = True
                break
    out = {
        "resultCode": listed.get("resultCode", 1) if isinstance(listed, dict) else 1,
        "resultMsg": listed.get("resultMsg") if isinstance(listed, dict) else None,
        "data": {
            "projectId": args.project_id,
            "employeeId": args.employee_id,
            "isMember": found,
            "checkMode": "listMembers",
            "note": "OpenAPI isProjectMember 仅支持当前调用人；本结果来自 listMembers",
        },
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
