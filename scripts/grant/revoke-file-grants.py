#!/usr/bin/env python3
"""POST /document-database/fileGrant/revokeGrants — 整单收回目录授权（勿用于单项减权）

逐人调用并汇总；鉴权失败短路，避免对后续人员重复打同一错误。
"""
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
from docdb_open_api import ensure_common_on_path, is_auth_error, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

API_PATH = "/document-database/fileGrant/revokeGrants"


def main():
    p = DocdbArgumentParser(hint="""revoke-file-grants.py 必须提供 --file-id 与 --emp-ids；真实写入还需 --confirm YES。
失败会按人列出；鉴权失败会短路后续人员。
示例: python3 -B <skill-dir>/scripts/grant/revoke-file-grants.py --file-id 12345 --emp-ids "1,2" --confirm YES
""")
    p.add_argument("--file-id", dest="file_id", required=True, type=int)
    p.add_argument("--emp-ids", required=True, help="逗号分隔的 employeeId")
    add_safety_args(p)
    args = p.parse_args()
    emp_ids = [int(x.strip()) for x in args.emp_ids.split(",") if x.strip()]
    if not emp_ids:
        print("错误: --emp-ids 不能为空", file=sys.stderr)
        sys.exit(1)
    preview = {"fileId": args.file_id, "employeeIds": emp_ids, "perEmp": True}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=preview)

    results = []
    failed = []
    for idx, eid in enumerate(emp_ids):
        body = {"fileId": args.file_id, "employeeIds": [eid]}
        try:
            result = request_open_api(API_PATH, method="POST", body=body, fatal=False)
        except Exception as e:
            results.append({"employeeId": eid, "ok": False, "error": str(e)})
            failed.append(eid)
            if is_auth_error(e):
                for rest in emp_ids[idx + 1 :]:
                    results.append({
                        "employeeId": rest,
                        "ok": False,
                        "skipped": True,
                        "error": "skipped: auth failed earlier",
                    })
                    failed.append(rest)
                break
            continue
        code = result.get("resultCode") if isinstance(result, dict) else None
        ok = code == 1
        results.append({"employeeId": eid, "ok": ok, "result": result})
        if not ok:
            failed.append(eid)

    out = {
        "resultCode": 1 if not failed else 0,
        "resultMsg": None if not failed else f"部分失败 employeeIds={failed}",
        "data": {"results": results, "failedEmployeeIds": failed},
    }
    print(json.dumps(out, ensure_ascii=False))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
