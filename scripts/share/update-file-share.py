#!/usr/bin/env python3
"""
share / updateFileShare 脚本

用途：更新文件/文件夹的协同分享（覆盖更新/新增/删除）。

注意：
  - 该接口通常需要先 getFileShares 拉取现有列表，再在此基础上修改后“全量提交”。
  - 如果提交的 shareGrants 缺少某些已存在对象，可能会被视为取消分享（取决于调用方权限与下游规则）。

使用方式：
  python3 scripts/share/update-file-share.py <file_id> '<share_grants_json>'

share_grants_json 示例：
  '[{"objectId":10001,"objectType":"person","permissions":["fileshare","preview","read"],"dueDate":20991231,"name":"张三"}]'

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

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


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share/updateFileShare"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if AUTH_MODE == "appKey":
        app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
        if not app_key:
            print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
            sys.exit(1)
        headers["appKey"] = app_key
    return headers


def call_api(body: dict) -> dict:
    headers = build_headers()
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="更新文件/文件夹协同分享（updateFileShare）")
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    parser.add_argument("share_grants_json", type=str, help="shareGrants JSON 数组字符串")
    args = parser.parse_args()

    try:
        share_grants = json.loads(args.share_grants_json)
    except Exception as e:
        print(f"错误: share_grants_json 不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(share_grants, list):
        print("错误: share_grants_json 必须是 JSON 数组", file=sys.stderr)
        sys.exit(1)

    body = {
        "fileId": args.file_id,
        "shareGrants": share_grants,
    }

    result = call_api(body)
    processed = process_result(result)
    print(json.dumps(processed, ensure_ascii=False))


if __name__ == "__main__":
    main()

