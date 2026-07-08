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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from docdb_open_api import get_file_basic_info  # noqa: E402


def main():
    import argparse

    p = argparse.ArgumentParser(description="根据 fileId 查询文件/文件夹基本信息")
    p.add_argument("file_id", type=int, help="文件或文件夹 ID")
    args = p.parse_args()
    data = get_file_basic_info(args.file_id)
    print(json.dumps({"resultCode": 1, "resultMsg": None, "data": data}, ensure_ascii=False))


if __name__ == "__main__":
    main()
