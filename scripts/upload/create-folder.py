#!/usr/bin/env python3
"""
upload / createFolder 脚本

用途：在指定空间/父目录下显式创建空文件夹（同步建目录、预置目录结构）

使用方式：
  python3 scripts/upload/create-folder.py <project_id> <parent_id> <name> [--cover] [--auto-rename]

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


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/createFolder"


def build_headers() -> dict:
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not app_key:
        print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
        sys.exit(1)
    return {"Content-Type": "application/json", "appKey": app_key}


def call_api(project_id: int, parent_id: int, name: str, cover: bool, auto_rename: bool) -> dict:
    body = {
        "projectId": project_id,
        "parentId": parent_id,
        "name": name,
        "cover": cover,
        "autoRename": auto_rename,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=build_headers(),
        method="POST",
    )

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

    parser = argparse.ArgumentParser(description="创建空文件夹")
    parser.add_argument("project_id", type=int, help="空间 projectId")
    parser.add_argument("parent_id", type=int, help="父目录 fileId，空间根传 0")
    parser.add_argument("name", type=str, help="文件夹名称（勿含 / 或 \\）")
    parser.add_argument("--cover", action="store_true", help="同名时覆盖（慎用）")
    parser.add_argument("--auto-rename", action="store_true", help="同名时自动重命名")
    args = parser.parse_args()

    result = call_api(args.project_id, args.parent_id, args.name, args.cover, args.auto_rename)
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
