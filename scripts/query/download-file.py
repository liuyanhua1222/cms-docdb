#!/usr/bin/env python3
"""
query / downloadFile 脚本

用途：下载文件到本地（先获取下载链接，再下载文件）

使用方式：

"""

import sys
import urllib.parse
import os
import json
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
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path, request_open_api
ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser

# 强制标准输出使用 UTF-8 编码，解决 Windows PowerShell 中文乱码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 接口完整 URL
API_PATH = "/document-database/file/getDownloadInfo"
CHUNK_SIZE = 5 * 1024 * 1024
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (1, 2, 4)


def get_download_url(file_id: int) -> dict:
    """获取文件下载链接"""
    params = [("fileId", str(file_id)), ("forceDownload", "true")]
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"

    return request_open_api(url, method="GET")

def download_file(download_url: str, output_path: str) -> str:
    """下载已签发的 URL（无需 OpenAPI 鉴权头）。"""
    import urllib.request
    for attempt in range(3):
        try:
            req = urllib.request.Request(download_url, method="GET")
            with urllib.request.urlopen(req, timeout=120) as resp, open(output_path, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return output_path
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                print(f"错误: 下载失败 - {e}", file=sys.stderr)
                sys.exit(1)

def main():
    parser = DocdbArgumentParser(description="下载文件到本地", hint="""download-file.py 必须提供 file_id。
优先省略 --output（默认写系统临时目录，读 stdout 路径）；禁止 shell 重定向。
示例: openapi_skill_exec skillCode=cms-docdb toolName=download-file argv=["12345"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""",
    )
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
