#!/usr/bin/env python3
"""
query / getDownloadInfo 脚本

用途：获取文件的下载链接或在线预览凭据

使用方式：
  python3 scripts/query/get-download-info.py <file_id> [--force-download] [--see-original]

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

# 接口完整 URL（与 openapi/query/get-download-info.md 中声明的一致）
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getDownloadInfo"
AUTH_MODE = "appKey"


def build_headers() -> dict:
    """根据鉴权模式构造请求头"""
    headers = {"Content-Type": "application/json"}

    if AUTH_MODE == "appKey":
        app_key = os.environ.get("XG_BIZ_API_KEY") or os.environ.get("XG_APP_KEY")
        if not app_key:
            print("错误: 请设置环境变量 XG_BIZ_API_KEY 或 XG_APP_KEY", file=sys.stderr)
            sys.exit(1)
        headers["appKey"] = app_key

    return headers


def call_api(file_id: int, force_download: bool = False, see_original: bool = None,
             source: str = None, version_number: int = None, bypass_risk: bool = None) -> dict:
    """调用获取下载/预览凭据接口，返回原始 JSON 响应"""
    headers = build_headers()

    params = [("fileId", str(file_id)), ("forceDownload", "true" if force_download else "false")]
    if see_original is not None:
        params.append(("seeOriginal", "true" if see_original else "false"))
    if source:
        params.append(("source", source))
    if version_number is not None:
        params.append(("versionNumber", str(version_number)))
    if bypass_risk is not None:
        params.append(("bypassRisk", "true" if bypass_risk else "false"))

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
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
    parser = argparse.ArgumentParser(description="获取文件下载或在线预览凭据")
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
