#!/usr/bin/env python3
"""
upload / get-file-download-info 脚本

用途：根据 resourceId 获取文件下载信息（临时下载 URL，有效期 1 小时）

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

# 接口完整 URL（与 openapi/upload/get-file-download-info.md 中声明的一致）
API_PATH = "/cwork-file/getDownloadInfo"


def call_api(resource_id: int) -> dict:
    """调用获取文件下载信息接口，返回原始 JSON 响应"""
    
    params = [("resourceId", str(resource_id))]
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"

    return request_open_api(url, method="GET")

def main():
    import argparse
    parser = DocdbArgumentParser(description="获取文件下载信息（临时下载 URL）",
        hint="""get-file-download-info.py 必须提供 resource_id。
示例: python3 -B <skill-dir>/scripts/upload/get-file-download-info.py 999；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("resource_id", type=int, nargs='?', help="资源 ID（位置参数）")
    parser.add_argument("--resource-id", type=int, dest="resource_id_opt", help="资源 ID（命名参数）")
    args = parser.parse_args()
    
    resource_id = args.resource_id or args.resource_id_opt
    if resource_id is None:
        print("错误: 请提供 resourceId", file=sys.stderr)
        sys.exit(1)

    result = call_api(resource_id)

    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
