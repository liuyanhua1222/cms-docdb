#!/usr/bin/env python3
"""
share / revokeFileShareGrants 脚本

用途：整单撤销指定员工的协同分享（人从分享列表消失；幂等；不发送钉钉通知）。
逐人调用并汇总；鉴权失败短路，避免对后续人员重复打同一错误。
"""

import sys
import os
import json

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

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)

API_PATH = "/document-database/share/revokeFileShareGrants"
VERIFY_PATH = "/document-database/share/getFileShares"


def _target_still_present(payload: dict, emp_id: int) -> bool:
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = data if isinstance(data, list) else (data.get("records", []) if isinstance(data, dict) else [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        target = row.get("empId", row.get("employeeId", row.get("objectId")))
        if str(target) == str(emp_id) and row.get("status", 1) in (1, "1", None):
            return True
    return False


def parse_emp_ids(raw: str) -> list:
    parts = [p.strip() for p in raw.split(",")]
    ids = []
    for p in parts:
        if not p:
            continue
        ids.append(int(p))
    if not ids:
        print("错误: --emp-ids 不能为空", file=sys.stderr)
        sys.exit(1)
    return ids


def main():
    parser = DocdbArgumentParser(description="撤销协同分享", hint="""revoke-file-share-grants.py 必须提供 --file-id，且必须带 --emp-ids。
真实写入还需 --confirm YES。失败会按人列出；鉴权失败会短路后续人员。
示例: python3 -B <skill-dir>/scripts/share/revoke-file-share-grants.py --file-id 12345 --emp-ids "1,2" --confirm YES
""")
    parser.add_argument("--file-id", dest="file_id", required=True, type=int, help="文件/文件夹 ID")
    parser.add_argument("--emp-ids", type=str, required=True, help="员工 empId 列表，逗号分隔")
    add_safety_args(parser)
    args = parser.parse_args()

    emp_ids = parse_emp_ids(args.emp_ids)
    preview_body = {"fileId": args.file_id, "empIds": emp_ids, "perEmp": True}
    enforce_or_dry_run(args, method="POST", url=API_PATH, body=preview_body)

    results = []
    failed = []
    for idx, eid in enumerate(emp_ids):
        body = {"fileId": args.file_id, "empIds": [eid]}
        try:
            result = request_open_api(API_PATH, method="POST", body=body, fatal=False)
        except Exception as e:
            results.append({"empId": eid, "ok": False, "error": str(e)})
            failed.append(eid)
            if is_auth_error(e):
                for rest in emp_ids[idx + 1 :]:
                    results.append({
                        "empId": rest,
                        "ok": False,
                        "skipped": True,
                        "error": "skipped: auth failed earlier",
                    })
                    failed.append(rest)
                break
            continue
        code = result.get("resultCode") if isinstance(result, dict) else None
        ok = code == 1
        direct_grant_status = "未确认"
        effective_status = "未验证"
        if ok:
            try:
                verify = request_open_api(
                    f"{VERIFY_PATH}?fileId={args.file_id}", method="GET", fatal=False
                )
                if _target_still_present(verify, eid):
                    ok = False
                    direct_grant_status = "仍存在"
                    result = {"revoke": result, "verify": verify, "verifyError": "撤销后仍存在有效分享"}
                else:
                    direct_grant_status = "直接授权已移除"
            except Exception as e:
                ok = False
                direct_grant_status = "未确认"
                result = {"revoke": result, "verifyError": f"撤销后复查失败: {e}"}
        results.append({
            "empId": eid,
            "ok": ok,
            "directGrantStatus": direct_grant_status,
            "effectivePermissionStatus": effective_status,
            "result": result,
        })
        if not ok:
            failed.append(eid)

    out = {
        "resultCode": 1 if not failed else 0,
        "resultMsg": None if not failed else f"部分失败 empIds={failed}",
        "data": {"results": results, "failedEmpIds": failed},
    }
    print(json.dumps(out, ensure_ascii=False))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
