#!/usr/bin/env python3
"""
manage / updateFileProperty — 已废弃，请改用 update-file-name.py / move-file.py

本脚本保留用于兼容旧命令行：自动转发到新接口（先 move 再 rename）。
原样转发 --dry-run / --confirm 给子脚本；自身缺 confirm 且非 dry-run 时 exit 2。
"""

import sys
import os
import json
import argparse
import subprocess

if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "common"))
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path
ensure_common_on_path(__file__)
from safety import add_safety_args


def run_script(script_name: str, args: list) -> dict:
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script_name)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        sys.exit(proc.returncode)
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(
        description="[已废弃] 转发到 update-file-name / move-file")
    parser.add_argument("file_id", type=int)
    parser.add_argument("--new-name", type=str)
    parser.add_argument("--target-parent-id", type=int)
    parser.add_argument("--cover", action="store_true")
    parser.add_argument("--auto-rename", action="store_true")
    add_safety_args(parser)
    args = parser.parse_args()

    if not args.dry_run and args.confirm != "YES":
        print(
            "错误: 写入类操作必须显式传入 --confirm YES"
            "（预览请求用 --dry-run）",
            file=sys.stderr,
        )
        sys.exit(2)

    print("警告: update-file-property 已废弃，正在转发到 updateFileName/moveFile", file=sys.stderr)

    if not args.new_name and not args.target_parent_id:
        print("错误: 必须提供 --new-name 或 --target-parent-id", file=sys.stderr)
        sys.exit(1)

    safety_flags = []
    if args.dry_run:
        safety_flags.append("--dry-run")
    if args.confirm:
        safety_flags.extend(["--confirm", args.confirm])

    move_strategy = "1" if args.cover else ("0" if args.auto_rename else "2")
    rename_strategy = "0" if args.auto_rename else "1"
    last = None

    if args.target_parent_id is not None:
        move_args = [
            str(args.file_id),
            "--target-parent-id", str(args.target_parent_id),
            "--name-conflict-strategy", move_strategy,
        ]
        if args.new_name:
            move_args.extend(["--new-name", args.new_name])
        move_args.extend(safety_flags)
        last = run_script("move-file.py", move_args)
    elif args.new_name:
        rename_args = [
            str(args.file_id),
            "--new-name", args.new_name,
            "--name-conflict-strategy", rename_strategy,
        ]
        rename_args.extend(safety_flags)
        last = run_script("update-file-name.py", rename_args)

    print(json.dumps(last, ensure_ascii=False))


if __name__ == "__main__":
    main()
