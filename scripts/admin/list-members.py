#!/usr/bin/env python3
"""GET /document-database/admin/listMembers — 查询空间成员列表（需管理员）"""
import sys
import os
import json
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

API_PATH = "/document-database/admin/listMembers"


def main():
    p = DocdbArgumentParser(hint="""list-members.py 必须提供 --project-id。
需空间管理员。返回按员工加入的成员（employeeId/name/role）。
组织授权请用 list-org-members.py。
示例: python3 -B <skill-dir>/scripts/admin/list-members.py --project-id 10001；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    args = p.parse_args()
    url = f"{API_PATH}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
    result = request_open_api(url, method="GET")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
