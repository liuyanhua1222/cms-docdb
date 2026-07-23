#!/usr/bin/env python3
"""
upload / uploadContent 脚本

用途：一键快速保存纯文本内容到个人知识库（AI 内容入库首选）

使用方式：
  python3 scripts/upload/upload-content.py

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
from cli_args import DocdbArgumentParser
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


# 接口完整 URL（与 openapi/upload/upload-content.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/uploadContent"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        headers["appKey"] = resolve_app_key()
    return headers


def call_api(content: str, file_name: str,
             file_suffix: str = None, folder_name: str = None,
             project_id: int = None,
             update_file_id: int = None, version_name: str = None,
             version_remark: str = None) -> dict:
    """调用一键上传接口，返回原始 JSON 响应"""
    headers = build_headers()

    body = {
        "content": content,
        "fileName": file_name
    }
    if file_suffix:
        body["fileSuffix"] = file_suffix
    if folder_name:
        body["folderName"] = folder_name
    if project_id is not None:
        body["projectId"] = project_id
    if update_file_id is not None:
        body["updateFileId"] = update_file_id
    if version_name:
        body["versionName"] = version_name
    if version_remark:
        body["versionRemark"] = version_remark

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
    parser = DocdbArgumentParser(description="一键保存纯文本内容到个人知识库或指定项目空间", hint="""upload-content.py 必须提供 content 与 file_name。
真实写入还需 --confirm YES（可先 --dry-run）。
示例: python3 -B <skill-dir>/scripts/upload/upload-content.py "正文" "报告.md" --confirm YES""")
    parser.add_argument("content", type=str, help="文件内容")
    parser.add_argument("file_name", type=str, help="文件名（建议带扩展名）")
    parser.add_argument("--file-suffix", type=str, help="文件后缀（md/html/txt/json）")
    parser.add_argument("--folder-name", type=str, help="逻辑目录路径，支持多级（仅新建模式有效）")
    parser.add_argument("--project-id", type=int, help="目标项目空间 ID，不传则保存到个人知识库")
    parser.add_argument("--update-file-id", type=int, help="版本更新模式：要更新的目标文件 ID，传入后切换为版本更新模式")
    parser.add_argument("--version-name", type=str, help="版本名称，如 V2.0（版本更新模式专用）")
    parser.add_argument("--version-remark", type=str, help="版本说明（版本更新模式专用）")
    add_safety_args(parser)
    args = parser.parse_args()

    body = {
        "content": args.content,
        "fileName": args.file_name,
    }
    if args.file_suffix:
        body["fileSuffix"] = args.file_suffix
    if args.folder_name:
        body["folderName"] = args.folder_name
    if args.project_id is not None:
        body["projectId"] = args.project_id
    if args.update_file_id is not None:
        body["updateFileId"] = args.update_file_id
    if args.version_name:
        body["versionName"] = args.version_name
    if args.version_remark:
        body["versionRemark"] = args.version_remark
    enforce_or_dry_run(args, method="POST", url=API_URL, body=body)

    result = call_api(
        content=args.content,
        file_name=args.file_name,
        file_suffix=args.file_suffix,
        folder_name=args.folder_name,
        project_id=args.project_id,
        update_file_id=args.update_file_id,
        version_name=args.version_name,
        version_remark=args.version_remark,
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
