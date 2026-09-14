#!/usr/bin/env python3
"""GET /document-database/admin/isProjectMember — 判断是否空间成员。

- 默认：查当前调用人
- `--employee-id`：查指定人（须空间管理员）；优先正式 OpenAPI；
  仅当响应能证明查的是目标人（data.employeeId 匹配）才采信；
  否则回退 listMembers（兼容旧网关忽略 query 的情况）
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
from project_member_check import check_other_member

API_PATH = "/document-database/admin/isProjectMember"


def main():
    p = DocdbArgumentParser(hint="""is-project-member.py 必须提供 --project-id。
默认检查当前调用人。预检他人请加 --employee-id（正式 API；不可信则回退 listMembers）。
示例: python3 -B <skill-dir>/scripts/admin/is-project-member.py --project-id 10001
示例: python3 -B <skill-dir>/scripts/admin/is-project-member.py --project-id 10001 --employee-id 2
""")
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    p.add_argument(
        "--employee-id",
        type=int,
        default=None,
        help="被查 employeeId；提供则走正式 API（须管理员），不可信时回退 listMembers",
    )
    args = p.parse_args()

    if args.employee_id is None:
        url = f"{API_PATH}?{urllib.parse.urlencode({'projectId': str(args.project_id)})}"
        result = request_open_api(url, method="GET")
        # 新 OpenAPI 自查也返回对象；旧版可能仍是 Boolean — 原样输出
        print(json.dumps(result, ensure_ascii=False))
        return

    print(json.dumps(check_other_member(args.project_id, args.employee_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
