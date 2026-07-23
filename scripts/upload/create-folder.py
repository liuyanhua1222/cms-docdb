#!/usr/bin/env python3
"""
upload / createFolder 脚本

用途：在指定空间/父目录下显式创建空文件夹（同步建目录、预置目录结构）

使用方式：
  python3 scripts/upload/create-folder.py <parent_id> <name> [--project-id <id>] [--cover] [--auto-rename]

  parentId != 0 时默认通过 getFileBasicInfo 自动解析 projectId。

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
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_project_id_for_parent, resolve_app_key
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


API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/createFolder"


def build_headers() -> dict:
    app_key = resolve_app_key()
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


def main():
    parser = DocdbArgumentParser(description="在指定父目录下创建文件夹", hint="""create-folder.py 必须提供 parent_id 与 name。
真实写入还需 --confirm YES（可先 --dry-run）。
示例: python3 -B <skill-dir>/scripts/upload/create-folder.py 0 "新产品" --confirm YES""")
    parser.add_argument("parent_id", type=int, help="父目录 fileId，空间根传 0")
    parser.add_argument("name", type=str, help="文件夹名称（勿含 / 或 \\）")
    parser.add_argument("--project-id", type=int, default=None, help="空间 ID；parentId!=0 时可省略（自动反查）")
    parser.add_argument("--no-resolve-project-id", action="store_true", help="不调用 getFileBasicInfo（不推荐）")
    parser.add_argument("--cover", action="store_true", help="同名时覆盖（慎用）")
    parser.add_argument("--auto-rename", action="store_true", help="同名时自动重命名")
    add_safety_args(parser)
    args = parser.parse_args()

    body_preview = {
        "projectId": args.project_id,
        "parentId": args.parent_id,
        "name": args.name,
        "cover": args.cover,
        "autoRename": args.auto_rename,
    }
    enforce_or_dry_run(
        args,
        method="POST",
        url=API_URL,
        body=body_preview,
        extra={"projectIdResolved": False},
    )
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
