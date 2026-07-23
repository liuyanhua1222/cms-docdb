#!/usr/bin/env python3
"""
query / downloadFile 脚本

用途：下载文件到本地（先获取下载链接，再下载文件）

使用方式：
  python3 scripts/query/download-file.py <file_id> [--output /path/to/save.pdf]

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import tempfile
import time

# --- cms-docdb common ---
_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
from docdb_open_api import ensure_common_on_path, ssl_context
ensure_common_on_path(__file__)

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


# 接口完整 URL
API_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database/file/getDownloadInfo"
AUTH_MODE = "appKey"
CHUNK_SIZE = 5 * 1024 * 1024
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (1, 2, 4)


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


def get_download_url(file_id: int) -> dict:
    """获取文件下载链接"""
    headers = build_headers()
    params = [("fileId", str(file_id)), ("forceDownload", "true")]
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers=headers, method="GET")

    ctx = ssl_context()

    opener = build_opener(ctx)

    for attempt in range(3):
        try:
            with opener.open(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                print(f"错误: 获取下载链接失败 - {e}", file=sys.stderr)
                sys.exit(1)


def download_file(download_url: str, output_path: str) -> str:
    """从 URL 下载文件到本地"""
    ctx = ssl_context()

    opener = build_opener(ctx)

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(download_url, method="GET")
            with opener.open(req, timeout=120) as resp, open(output_path, 'wb') as f:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
            return output_path
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS[attempt])
            else:
                print(f"错误: 下载文件失败 - {e}", file=sys.stderr)
                sys.exit(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="下载文件到本地")
    parser.add_argument("file_id", type=int, help="文件 ID")
    parser.add_argument("--output", type=str, help="输出文件路径（可选，默认保存到临时目录）")
    args = parser.parse_args()

    # 1. 获取下载链接
    result = get_download_url(args.file_id)
    
    if result.get('resultCode') != 1:
        print(json.dumps({
            'resultCode': result.get('resultCode'),
            'resultMsg': result.get('resultMsg', '获取下载链接失败'),
            'data': None
        }, ensure_ascii=False))
        sys.exit(1)
    
    data = result.get('data', {})
    download_url = data.get('downloadUrl') or data.get('url')
    file_name = data.get('fileName', f'file_{args.file_id}')
    
    if not download_url:
        print(json.dumps({
            'resultCode': 0,
            'resultMsg': '未获取到下载链接',
            'data': None
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 2. 确定输出路径
    if args.output:
        output_path = args.output
    else:
        # 使用临时目录
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, file_name)
    
    # 3. 下载文件
    saved_path = download_file(download_url, output_path)
    
    # 4. 返回结果
    print(json.dumps({
        'resultCode': 1,
        'resultMsg': None,
        'data': {
            'fileId': args.file_id,
            'fileName': file_name,
            'localPath': saved_path,
            'fileSize': os.path.getsize(saved_path)
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
