#!/usr/bin/env python3
"""
share / upsert（存在则更新，不存在则新增）

用途：
  针对“同一人重复授权 add 返回成功但不生效”的问题，提供一个安全的 upsert 脚本：
  - 授权前先 getFileShares 判断该 empId 是否已存在
  - 已存在：通过 updateFileShare 更新（并保留其他人的授权，避免误删）
  - 不存在：调用 addFileShare 新增授权

使用方式：
  python3 scripts/share/upsert-file-share-grant.py <file_id> --emp-id <emp_id> [--permissions "read,preview,download"] [--due-date 20991231] [--name "张三"] [--no-notice] [--source "open_api"]

环境变量：
  XG_BIZ_API_KEY / XG_APP_KEY — appKey（由 cms-auth-skills 预先准备）
"""

import sys
import os
import json
import urllib.request
import urllib.parse
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


BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/share"
URL_GET_FILE_SHARES = f"{BASE}/getFileShares"
URL_ADD_FILE_SHARE = f"{BASE}/addFileShare"
URL_UPDATE_FILE_SHARE = f"{BASE}/updateFileShare"
URL_GET_SHARE_URL = f"{BASE}/getShareUrl"

DEFAULT_PERMISSIONS = ["fileshare", "preview", "read"]
DEFAULT_DUE_DATE = 20991231


def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
    if not app_key:
        print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
        sys.exit(1)
    headers["appKey"] = app_key
    return headers


def call_json(method: str, url: str, body: dict = None, params: list = None) -> dict:
    headers = build_headers()
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

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


def parse_permissions(raw: str):
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",")]
    perms = [p for p in parts if p]
    return perms or None


def get_file_shares(file_id: int):
    return call_json("GET", URL_GET_FILE_SHARES, params=[("fileId", str(file_id))])


def add_file_share(file_id: int, emp_id: int, permissions: list, due_date: int, name: str, send_notice: bool):
    grant = {"empId": emp_id, "permissions": permissions, "dueDate": due_date}
    if name:
        grant["name"] = name
    body = {"fileId": file_id, "isSendNotice": send_notice, "shareGrants": [grant]}
    return call_json("POST", URL_ADD_FILE_SHARE, body=body)


def update_file_share(file_id: int, all_grants: list):
    body = {"fileId": file_id, "shareGrants": all_grants}
    return call_json("POST", URL_UPDATE_FILE_SHARE, body=body)


def get_share_url(file_id: int, source: str = None):
    params = [("fileId", str(file_id))]
    if source:
        params.append(("source", source))
    return call_json("GET", URL_GET_SHARE_URL, params=params)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="对单个 empId 做 upsert 授权：存在则更新，不存在则新增")
    parser.add_argument("file_id", type=int, help="文件/文件夹 ID")
    parser.add_argument("--emp-id", type=int, required=True, help="被分享对象的员工 empId（必填）")
    parser.add_argument("--permissions", type=str, help='权限列表，逗号分隔；不传则默认 "fileshare,preview,read"')
    parser.add_argument("--due-date", type=int, help="到期日期（yyyyMMdd）；不传默认 20991231（长期有效）")
    parser.add_argument("--name", type=str, help="被分享人姓名（可选）")
    parser.add_argument("--no-notice", action="store_true", help="不发送钉钉分享通知（默认发送，仅对新增生效）")
    parser.add_argument("--source", type=str, help="生成短链的 source（可选）")
    parser.add_argument("--print-share-url", action="store_true", help="成功后额外输出 shareUrl")
    args = parser.parse_args()

    perms = parse_permissions(args.permissions) or DEFAULT_PERMISSIONS
    due_date = args.due_date if args.due_date is not None else DEFAULT_DUE_DATE
    send_notice = False if args.no_notice else True

    current = get_file_shares(args.file_id)
    shares = current.get("data") if isinstance(current, dict) else None
    if shares is None:
        shares = []

    exists = False
    for item in shares:
        if item.get("objectType") == "person" and int(item.get("objectId")) == int(args.emp_id):
            exists = True
            break

    if not exists:
        resp = add_file_share(args.file_id, args.emp_id, perms, due_date, args.name, send_notice)
        action = "created"
    else:
        # 保留所有现有授权对象，仅替换目标 empId 的 permissions/dueDate/name
        grants = []
        for item in shares:
            grant = {
                "objectId": item.get("objectId"),
                "objectType": item.get("objectType"),
                "permissions": item.get("permissions") or [],
                "dueDate": item.get("dueDate") or DEFAULT_DUE_DATE,
                "name": item.get("name"),
            }
            if item.get("objectType") == "person" and int(item.get("objectId")) == int(args.emp_id):
                grant["permissions"] = perms
                grant["dueDate"] = due_date
                if args.name:
                    grant["name"] = args.name
            grants.append(grant)

        # 如果现有分享列表里没有找到（理论上不会），则追加
        if not any(g.get("objectType") == "person" and int(g.get("objectId")) == int(args.emp_id) for g in grants):
            grants.append(
                {
                    "objectId": args.emp_id,
                    "objectType": "person",
                    "permissions": perms,
                    "dueDate": due_date,
                    "name": args.name,
                }
            )

        resp = update_file_share(args.file_id, grants)
        action = "updated"

    out = {"action": action, "result": resp}

    if args.print_share_url:
        url_resp = get_share_url(args.file_id, source=args.source if args.source else None)
        out["shareUrl"] = url_resp.get("data") if isinstance(url_resp, dict) else None

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

