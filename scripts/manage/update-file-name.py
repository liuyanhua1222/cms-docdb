#!/usr/bin/env python3
"""
manage / updateFileName — 同目录改名（同步 Open API）

使用方式：
  python3 scripts/manage/update-file-name.py <file_id> --new-name "B.md" [--name-conflict-strategy 1]

运行时变量：appkey
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
from docdb_open_api import ensure_common_on_path, ssl_context
ensure_common_on_path(__file__)
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/updateFileName"


def build_headers():
    headers = {"Content-Type": "application/json"}
    app_key = os.environ.get("appkey")
    if not app_key:
        print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr)
        sys.exit(1)
    headers["appKey"] = app_key
    return headers


def post_json(body: dict) -> dict:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers=build_headers(),
        method="POST",
    )
    ctx = ssl_context()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                print(f"错误: HTTP {e.code}", file=sys.stderr)
                try:
                    print(e.read().decode("utf-8"), file=sys.stderr)
                except Exception:
                    pass
                sys.exit(1)
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="同目录改名（updateFileName）")
    parser.add_argument("file_id", type=int, help="文件或文件夹 ID")
    parser.add_argument("--new-name", required=True, help="新名称")
    parser.add_argument("--project-id", type=int, help="空间 ID（建议传入）")
    parser.add_argument("--name-conflict-strategy", type=int, default=1,
                        help="0=自动重命名，1=失败（默认）")
    parser.add_argument("--root-file-id", type=int, help="映射根，用于返回 relativePath")
    add_safety_args(parser)
    args = parser.parse_args()

    body = {
        "fileId": args.file_id,
        "newName": args.new_name,
        "nameConflictStrategy": args.name_conflict_strategy,
    }
    if args.project_id is not None:
        body["projectId"] = args.project_id
    if args.root_file_id is not None:
        body["rootFileId"] = args.root_file_id

    enforce_or_dry_run(args, method="POST", url=API_URL, body=body)
    result = post_json(body)
    print(json.dumps({
        "resultCode": result.get("resultCode"),
        "resultMsg": result.get("resultMsg"),
        "data": result.get("data"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
