#!/usr/bin/env python3
"""
share / revokeFileShareGrants 脚本

用途：撤销指定员工对文件/文件夹的协同分享（幂等；不发送钉钉通知）

使用方式：
  python3 scripts/share/revoke-file-share-grants.py <file_id> --emp-ids 10002,10003

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
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
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_app_key
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
if sys.stderr.encoding != "utf-8":
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)

    def http_error_302(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)

    def http_error_303(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)

    def http_error_307(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)

    def http_error_308(self, req, fp, code, msg, headers):
        return self.redirect_request(req, fp, code, msg, headers)


def build_opener(ctx):
    handlers = [CustomRedirectHandler()]
    if ctx:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share/revokeFileShareGrants"


def build_headers() -> dict:
    app_key = resolve_app_key()
    return {"Content-Type": "application/json", "appKey": app_key}


def call_api(file_id: int, emp_ids: list) -> dict:
    body = {"fileId": file_id, "empIds": emp_ids}
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=build_headers(),
        method="POST",
    )

    ctx = ssl_context()
    opener = build_opener(ctx)

    for attempt in range(3):
        try:
            with opener.open(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if attempt < 2:
                import time

                time.sleep(1)
            else:
                try:
                    err_body = e.read().decode("utf-8")
                    print(f"错误: HTTP {e.code} - {e.reason} - {err_body}", file=sys.stderr)
                except Exception:
                    print(f"错误: HTTP {e.code} - {e.reason}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            if attempt < 2:
                import time

                time.sleep(1)
            else:
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)


def process_result(result):
    if isinstance(result, dict):
        return {
            "resultCode": result.get("resultCode"),
            "resultMsg": result.get("resultMsg"),
            "data": result.get("data"),
        }
    return result


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
    parser = DocdbArgumentParser(description="撤销协同分享", hint="""revoke-file-share-grants.py 必须提供 file_id，且必须带 --emp-ids。
真实写入还需 --confirm YES。
示例: python3 -B <skill-dir>/scripts/share/revoke-file-share-grants.py 12345 --emp-ids 1,2 --confirm YES""")
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    parser.add_argument("--emp-ids", type=str, required=True, help="员工 empId 列表，逗号分隔")
    add_safety_args(parser)
    args = parser.parse_args()

    emp_ids = parse_emp_ids(args.emp_ids)
    body = {"fileId": args.file_id, "empIds": emp_ids}
    enforce_or_dry_run(args, method="POST", url=API_URL, body=body)
    result = call_api(args.file_id, emp_ids)
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
