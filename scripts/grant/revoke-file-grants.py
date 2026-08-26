#!/usr/bin/env python3
"""POST /document-database/fileGrant/revokeGrants — 整单收回目录授权（勿用于单项减权）"""
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
from safety import add_safety_args, enforce_or_dry_run

API_PATH = "/document-database/fileGrant/revokeGrants"


def main():
    p = DocdbArgumentParser(hint="""revoke-file-grants.py 必须提供 file_id 与 --emp-ids；真实写入还需 --confirm YES。
示例: openapi_skill_exec skillCode=cms-docdb toolName=revoke-file-grants argv=["12345", "--emp-ids", "1,2", "--confirm", "YES"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    p.add_argument("file_id", type=int)
    p.add_argument("--emp-ids", required=True, help="逗号分隔的 employeeId")
    add_safety_args(p)
    args = p.parse_args()
    body = {
        "fileId": args.file_id,
        "employeeIds": [int(x.strip()) for x in args.emp_ids.split(",") if x.strip()],
    }
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = request_open_api(API_PATH, method="POST", body=body)
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
