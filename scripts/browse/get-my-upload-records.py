#!/usr/bin/env python3
"""
browse / getMyUploadRecords 脚本

用途：分页查询当前用户在全空间的上传/新建记录（固定操作类型，默认近 90 天）

使用方式：
  python3 scripts/browse/get-my-upload-records.py [--page-index 1] [--page-size 20] [--project-id <id>] [--start-time <ms>] [--end-time <ms>]

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.parse
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


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/operationLog/getMyUploadRecords"


def build_headers() -> dict:
    app_key = resolve_app_key()
    return {"appKey": app_key}


def call_api(page_index=None, page_size=None, project_id=None, start_time=None, end_time=None) -> dict:
    params = []
    if page_index is not None:
        params.append(("pageIndex", str(page_index)))
    if page_size is not None:
        params.append(("pageSize", str(page_size)))
    if project_id is not None:
        params.append(("projectId", str(project_id)))
    if start_time is not None:
        params.append(("startTime", str(start_time)))
    if end_time is not None:
        params.append(("endTime", str(end_time)))

    url = API_URL
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=build_headers(), method="GET")

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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="分页查询当前用户全空间上传记录（默认近90天）")
    parser.add_argument("--page-index", type=int, help="页码，从1开始")
    parser.add_argument("--page-size", type=int, help="每页条数，最大100")
    parser.add_argument("--project-id", type=int, help="限定某一空间")
    parser.add_argument("--start-time", type=int, help="开始时间戳（毫秒）")
    parser.add_argument("--end-time", type=int, help="结束时间戳（毫秒）")
    args = parser.parse_args()

    result = call_api(
        page_index=args.page_index,
        page_size=args.page_size,
        project_id=args.project_id,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
