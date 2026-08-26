#!/usr/bin/env python3
"""
browse / getMyRecentUsed 脚本

用途：分页查询当前用户最近使用记录（固定 file_online_read、file_download、upload2agent）

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

API_PATH = "/document-database/operationLog/getMyRecentUsed"


def main():
    p = DocdbArgumentParser(hint="""get-my-recent-used.py get-my-recent-used 按业务参数调用（无必填时可传空 argv）。
示例: openapi_skill_exec skillCode=cms-docdb toolName=get-my-recent-used argv=["--page-index", "1"]；缺参补齐后用同一 toolName 重试，禁止改用标准 exec
""")
    p.add_argument("--page-index", type=int, default=1)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--biz-code", default=None)
    args = p.parse_args()
    q = [("pageIndex", str(args.page_index)), ("pageSize", str(args.page_size))]
    if args.biz_code:
        q.append(("bizCode", args.biz_code))
    url = f"{API_PATH}?{urllib.parse.urlencode(q)}"
    result = request_open_api(url, method="GET")
    print(json.dumps(result, ensure_ascii=False))
if __name__ == "__main__":
    main()
