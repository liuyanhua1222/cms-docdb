#!/usr/bin/env python3
"""
query / getDownloadInfo 脚本

用途：获取文件的下载链接或在线预览凭据

使用方式：

"""

import sys
import urllib.parse
import os
import json

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL（与 openapi/query/get-download-info.md 中声明的一致）
API_PATH = "/document-database/file/getDownloadInfo"


def call_api(file_id: int, force_download: bool = False, see_original: bool = None,
             source: str = None, version_number: int = None, bypass_risk: bool = None) -> dict:
    """调用获取下载/预览凭据接口，返回原始 JSON 响应"""
    
    params = [("fileId", str(file_id)), ("forceDownload", "true" if force_download else "false")]
    if see_original is not None:
        params.append(("seeOriginal", "true" if see_original else "false"))
    if source:
        params.append(("source", source))
    if version_number is not None:
        params.append(("versionNumber", str(version_number)))
    if bypass_risk is not None:
        params.append(("bypassRisk", "true" if bypass_risk else "false"))

    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"

    return request_open_api(url, method="GET")

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
    parser = DocdbArgumentParser(description="获取下载或预览凭据", hint="""get-download-info.py 必须提供 file_id。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-download-info argv=["12345"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--force-download", action="store_true", help="true 则返回下载链接，false 则返回预览凭据")
    parser.add_argument("--see-original", action="store_true", help="预览是否查看原文")
    parser.add_argument("--source", type=str, help="来源")
    parser.add_argument("--version-number", type=int, help="版本号")
    parser.add_argument("--bypass-risk", action="store_true", help="是否绕过风险检查")
    args = parser.parse_args()

    result = call_api(
        file_id=args.file_id,
        force_download=args.force_download,
        see_original=args.see_original if "--see-original" in sys.argv else None,
        source=args.source if args.source else None,
        version_number=args.version_number if args.version_number else None,
        bypass_risk=args.bypass_risk if args.bypass_risk else None
    )

    processed_result = process_result(result)
    print(json.dumps(processed_result, ensure_ascii=False))

if __name__ == "__main__":
    main()
