#!/usr/bin/env python3
"""GET /document-database/admin/isProjectMember — 判断当前用户是否空间成员"""
import sys, os, json

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


def main():
    p = DocdbArgumentParser(hint="""is-project-member.py 必须提供 project_id。
示例: python3 -B <skill-dir>/scripts/admin/is-project-member.py 10001；缺参补齐后用同一 python 命令重试
""")
    p.add_argument("project_id", type=int)
    args = p.parse_args()
    url = f"{API_PATH}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
    result = request_open_api(url, method="GET")
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
