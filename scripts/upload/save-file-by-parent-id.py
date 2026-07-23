#!/usr/bin/env python3
"""
upload / saveFileByParentId 脚本

用途：已知目标文件夹 ID 时，将物理文件保存到项目目录（比 saveFileByPath 少一次路径解析）

使用方式：
  python3 scripts/upload/save-file-by-parent-id.py <parent_id> <resource_id> "文件名.pdf" [--project-id <id>] [--suffix pdf] [--size 12345]

  parentId != 0 时默认通过 getFileBasicInfo 自动解析 projectId（避免 projectId 与 parentId 不一致）。
  parentId == 0（空间根）时必须传 --project-id。

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
from docdb_open_api import ensure_common_on_path, ssl_context, resolve_project_id_for_parent
ensure_common_on_path(__file__)
from safety import add_safety_args, enforce_or_dry_run

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    """自定义重定向处理器，显式支持 307/308 重定向并保留请求方法和请求体"""
    
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
    """构建支持 307/308 重定向的自定义 opener"""
    handlers = [CustomRedirectHandler()]
    if ctx:
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)


# 接口完整 URL（与 openapi/upload/save-file-by-parent-id.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/saveFileByParentId"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        app_key = os.environ.get("appkey")
        if not app_key:
            print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr)
            sys.exit(1)
        headers["appKey"] = app_key

    return headers


def call_api(project_id: int, parent_id: int, resource_id: int, name: str,
             suffix: str = None, size: int = None, is_sensitive: int = None) -> dict:
    """调用按父ID保存文件接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {
        "projectId": project_id,
        "parentId": parent_id,
        "resourceId": resource_id,
        "name": name,
        "fileType": "file"
    }
    if suffix:
        body["suffix"] = suffix
    if size is not None:
        body["size"] = size
    if is_sensitive is not None:
        body["isSensitive"] = is_sensitive

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST"
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
    """处理 API 响应结果，优先按 resultCode、resultMsg、data 读取"""
    if isinstance(result, dict):
        # 优先读取 resultCode、resultMsg、data
        result_code = result.get('resultCode')
        result_msg = result.get('resultMsg')
        data = result.get('data')
        
        # 构建标准化输出
        processed = {
            'resultCode': result_code,
            'resultMsg': result_msg,
            'data': data
        }
        return processed
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="将物理文件保存到指定父目录")
    parser.add_argument("parent_id", type=int, help="目标文件夹 ID（根目录传 0）")
    parser.add_argument("resource_id", type=int, help="资源 ID（必须）")
    parser.add_argument("name", type=str, help="保存的文件名")
    parser.add_argument("--project-id", type=int, default=None, help="空间 ID；parentId!=0 时可省略（自动反查）")
    parser.add_argument("--no-resolve-project-id", action="store_true",
                        help="不调用 getFileBasicInfo，直接使用 --project-id（不推荐）")
    parser.add_argument("--suffix", type=str, help="文件后缀")
    parser.add_argument("--size", type=int, help="文件大小（字节）")
    parser.add_argument("--is-sensitive", type=int, choices=[0, 1], help="是否敏感文件（0 否，1 是）")
    add_safety_args(parser)
    args = parser.parse_args()

    body_preview = {
        "projectId": args.project_id,
        "parentId": args.parent_id,
        "resourceId": args.resource_id,
        "name": args.name,
        "fileType": "file",
    }
    if args.suffix:
        body_preview["suffix"] = args.suffix
    if args.size is not None:
        body_preview["size"] = args.size
    if args.is_sensitive is not None:
        body_preview["isSensitive"] = args.is_sensitive
    enforce_or_dry_run(
        args,
        method="POST",
        url=API_URL,
        body=body_preview,
        extra={"projectIdResolved": False},
    )

    if args.no_resolve_project_id:
        if args.project_id is None:
            print("错误: --no-resolve-project-id 模式下必须提供 --project-id", file=sys.stderr)
            sys.exit(1)
        project_id = args.project_id
    else:
        project_id = resolve_project_id_for_parent(args.parent_id, args.project_id)

    result = call_api(
        project_id=project_id,
        parent_id=args.parent_id,
        resource_id=args.resource_id,
        name=args.name,
        suffix=args.suffix,
        size=args.size,
        is_sensitive=args.is_sensitive
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
