#!/usr/bin/env python3
"""
browse / getFileBasicInfo 脚本

用途：根据 fileId 查询文件或文件夹的基础元数据（含 projectId、type、parentId 等）

使用方式：
  python3 scripts/browse/get-file-basic-info.py <file_id>

运行时变量：
  appkey — 由小龙虾运行时上下文注入
"""

import json
import os
import sys

_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
from docdb_open_api import ensure_common_on_path, get_file_basic_info
ensure_common_on_path(__file__)


def main():
    import argparse

    p = argparse.ArgumentParser(description="根据 fileId 查询文件/文件夹基本信息")
    p.add_argument("file_id", type=int, help="文件或文件夹 ID")
    args = p.parse_args()
    data = get_file_basic_info(args.file_id)
    print(json.dumps({"resultCode": 1, "resultMsg": None, "data": data}, ensure_ascii=False))


if __name__ == "__main__":
    main()
