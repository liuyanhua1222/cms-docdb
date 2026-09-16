#!/usr/bin/env python3
"""
query / getDownloadInfo 脚本

用途：获取文件的下载链接或在线预览凭据

使用方式：
  python3 -B <skill-dir>/scripts/query/get-download-info.py --file-id 12345

"""

import sys
import urllib.parse
import os
import json
import argparse

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

def process_result(result, *, force_download=False):
    """保留服务端结果码，并标注当前模式下的正式 URL 是否可用。"""
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
        if result_code == 1 and isinstance(data, dict):
            selected_field = 'downloadUrl' if force_download else 'previewUrl'
            selected_url = data.get(selected_field)
            mode = 'download' if force_download else 'previewUrl'
            normalized_data = dict(
                data,
                selectedUrl=selected_url,
                urlMode=mode,
                urlAvailable=bool(selected_url),
            )
            if not selected_url:
                normalized_data['urlError'] = (
                    f'接口成功但未返回正式 {selected_field}，拒绝回退到其他链路'
                )
            processed['data'] = normalized_data
        return processed
    return result


def is_result_usable(result):
    """服务端成功且当前模式的正式 URL 存在时，CLI 才以成功退出。"""
    if not isinstance(result, dict) or result.get('resultCode') != 1:
        return False
    data = result.get('data')
    return isinstance(data, dict) and data.get('urlAvailable') is True

def main():
    parser = DocdbArgumentParser(description="获取下载或预览凭据", hint="""get-download-info.py 必须提供 --file-id。
示例: python3 -B <skill-dir>/scripts/query/get-download-info.py --file-id 12345；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("--file-id", dest="file_id", required=True, type=int, help="文件 ID")
    parser.add_argument("--force-download", action="store_true", help="true 则返回下载链接，false 则返回预览凭据")
    parser.add_argument("--see-original", action="store_true", help="预览是否查看原文")
    parser.add_argument("--source", type=str, help="来源")
    parser.add_argument("--version-number", type=int, help="版本号")
    parser.add_argument(
        "--bypass-risk",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    bypass_risk = None
    if args.bypass_risk:
        if os.environ.get("CMS_DOCDB_ALLOW_BYPASS_RISK") != "1":
            print(
                "错误: --bypass-risk 已禁用；须设置 CMS_DOCDB_ALLOW_BYPASS_RISK=1。"
                "注意：此参数表示用户二次确认，不是运维特权；"
                "现网下载多为 HARD_BLOCK 时传 true 仍会被拦。",
                file=sys.stderr,
            )
            sys.exit(2)
        print(
            "警告: 已启用 bypassRisk（用户二次确认凭证，非运维特权）。"
            "现网下载规则多为 HARD_BLOCK，本参数对下载往往无效；"
            "HARD_BLOCK 解封请走管理端 riskAlert，勿反复重试 bypass。",
            file=sys.stderr,
        )
        bypass_risk = True

    result = call_api(
        file_id=args.file_id,
        force_download=args.force_download,
        see_original=args.see_original if "--see-original" in sys.argv else None,
        source=args.source if args.source else None,
        version_number=args.version_number if args.version_number else None,
        bypass_risk=bypass_risk,
    )

    processed_result = process_result(result, force_download=args.force_download)
    print(json.dumps(processed_result, ensure_ascii=False))
    if not is_result_usable(processed_result):
        sys.exit(1)

if __name__ == "__main__":
    main()
