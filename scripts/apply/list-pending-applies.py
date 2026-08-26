#!/usr/bin/env python3
"""POST /document-database/fileGrant/apply/pending — 待我处理的申请"""
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

API_PATH = "/document-database/fileGrant/apply/pending"


def main():
    p = DocdbArgumentParser(hint="""list-pending-applies.py list-pending-applies 按业务参数调用（无必填时可传空 argv）。
示例: openapi_skill_exec skillCode=cms-docdb toolName=list-pending-applies argv=["--page-index", "1"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--file-name", default=None)
    p.add_argument("--keyword", default=None, help="统一关键字，模糊匹配申请人姓名/文件名/申请事由")
    p.add_argument("--proposer", default=None, help="申请人姓名筛选")
    args = p.parse_args()
    body = {"pageIndex": args.page_index, "pageSize": args.page_size}
    if args.file_name: body["fileName"] = args.file_name
    if args.keyword: body["keyword"] = args.keyword
    if args.proposer: body["proposer"] = args.proposer
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
