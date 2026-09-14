#!/usr/bin/env python3
"""临时成员闭环（P0-7）：list → add → list → remove → list。

真实写入须 --confirm YES，且 --ack-space-expand YES / --ack-space-shrink YES。
可先 --dry-run 校验参数与步骤顺序（子脚本 dry-run 不发业务 HTTP）。
"""
import sys
import os
import json
import subprocess

_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.abspath(os.path.join(_cms_here, "..", "common"))
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args


def _run(script: str, argv: list) -> dict:
    cmd = [sys.executable, "-B", os.path.join(_cms_here, script), *argv]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        print(proc.stderr or out or f"{script} exit {proc.returncode}", file=sys.stderr)
        sys.exit(proc.returncode)
    return json.loads(out) if out else {}


def _member_ids(payload: dict) -> list:
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    ids = []
    for row in data:
        if not isinstance(row, dict):
            continue
        eid = row.get("employeeId") or row.get("empId") or row.get("id")
        if eid is not None:
            ids.append(int(eid))
    return sorted(set(ids))


def main():
    p = DocdbArgumentParser(
        hint="""temp-member-lifecycle.py 必须提供 --project-id --employee-id。
示例: python3 -B <skill-dir>/scripts/admin/temp-member-lifecycle.py --project-id 10001 --employee-id 1 --ack-space-expand YES --ack-space-shrink YES --dry-run
"""
    )
    p.add_argument("--project-id", dest="project_id", required=True, type=int)
    p.add_argument("--employee-id", type=int, required=True)
    p.add_argument("--ack-space-expand", default="", help="加成员确认，真实写入须 YES")
    p.add_argument("--ack-space-shrink", default="", help="移除确认，真实写入须 YES")
    p.add_argument("--skip-remove", action="store_true")
    add_safety_args(p)
    args = p.parse_args()

    app_key_args = []
    if getattr(args, "app_key", None):
        app_key_args = ["--app-key", args.app_key]

    write_flags = list(app_key_args)
    if args.dry_run:
        write_flags.append("--dry-run")
    elif args.confirm:
        write_flags.extend(["--confirm", args.confirm])

    if not args.dry_run:
        if args.confirm != "YES":
            print("错误: 真实闭环须 --confirm YES（或先 --dry-run）", file=sys.stderr)
            sys.exit(2)
        if args.ack_space_expand != "YES":
            print("错误: 须 --ack-space-expand YES", file=sys.stderr)
            sys.exit(2)
        if not args.skip_remove and args.ack_space_shrink != "YES":
            print("错误: 须 --ack-space-shrink YES", file=sys.stderr)
            sys.exit(2)

    expand = args.ack_space_expand or "YES"
    shrink = args.ack_space_shrink or "YES"
    # 编排器的 dry-run 必须全链路离线；否则 list-members 会先发真实 GET，
    # 与脚本帮助所承诺的“不发业务 HTTP”相矛盾。
    list_args = ["--project-id", str(args.project_id), *app_key_args]
    if args.dry_run:
        list_args.append("--dry-run")
    steps = []

    before = _run("list-members.py", list_args)
    steps.append({"step": "list_before", "employeeIds": _member_ids(before)})

    add_result = _run(
        "add-member.py",
        [
            "--project-id", str(args.project_id),
            "--employee-id", str(args.employee_id),
            "--ack-space-expand", expand,
            *write_flags,
        ],
    )
    steps.append({"step": "add", "result": add_result if args.dry_run else {"resultCode": add_result.get("resultCode")}})

    mid = _run("list-members.py", list_args)
    mid_ids = _member_ids(mid)
    steps.append({
        "step": "list_after_add",
        "employeeIds": mid_ids,
        "containsTarget": args.employee_id in mid_ids or bool(args.dry_run),
    })

    if not args.skip_remove:
        rem = _run(
            "remove-member.py",
            [
                "--project-id", str(args.project_id),
                "--employee-id", str(args.employee_id),
                "--ack-space-shrink", shrink,
                *write_flags,
            ],
        )
        steps.append({"step": "remove", "result": rem if args.dry_run else {"resultCode": rem.get("resultCode")}})
        after = _run("list-members.py", list_args)
        after_ids = _member_ids(after)
        steps.append({
            "step": "list_after_remove",
            "employeeIds": after_ids,
            "containsTarget": args.employee_id in after_ids,
        })

    print(json.dumps({"resultCode": 1, "resultMsg": None, "data": {"lifecycle": steps}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
