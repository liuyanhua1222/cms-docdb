#!/usr/bin/env python3
"""
upload / uploadContent 脚本

用途：一键快速保存纯文本内容到个人知识库（AI 内容入库首选）

使用方式：
  python3 -B <skill-dir>/scripts/upload/upload-content.py --content "正文" --file-name "报告.md" --confirm YES

"""

import sys
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
from safety import add_safety_args, enforce_or_dry_run

if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if sys.stderr.encoding != 'utf-8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

API_PATH = "/document-database/file/uploadContent"


def normalize_file_name(file_name: str, file_suffix: str = None) -> tuple:
    """返回 (fileName, fileSuffix)；避免 .md.md。"""
    name = (file_name or "").strip()
    suffix = (file_suffix or "").strip().lstrip(".")
    if suffix:
        lower = name.lower()
        ext = f".{suffix.lower()}"
        if lower.endswith(ext):
            suffix = None  # 文件名已含后缀，不再传 fileSuffix 以免服务端再拼
        elif "." not in os.path.basename(name):
            name = f"{name}.{suffix}"
            suffix = None
    return name, suffix


def call_api(body: dict) -> dict:
    return request_open_api(API_PATH, method="POST", body=body)


def process_result(result):
    if isinstance(result, dict):
        return {
            'resultCode': result.get('resultCode'),
            'resultMsg': result.get('resultMsg'),
            'data': result.get('data'),
        }
    return result


def main():
    parser = DocdbArgumentParser(description="一键保存纯文本内容到个人知识库或指定项目空间", hint="""upload-content.py 必须提供 --content 与 --file-name。
真实写入还需 --confirm YES（可先 --dry-run）。
--folder-name 传空串会原样下发 folderName=""（不以真值判断丢弃）。
示例: python3 -B <skill-dir>/scripts/upload/upload-content.py --content "正文" --file-name "报告.md" --confirm YES；缺参补齐后用同一 python 命令重试
""")
    parser.add_argument("--content", type=str, required=True, help="文件内容")
    parser.add_argument("--file-name", dest="file_name", type=str, required=True, help="文件名（建议带扩展名）")
    parser.add_argument("--file-suffix", type=str, help="文件后缀（md/html/txt/json）；若文件名已含同后缀则忽略，防 .md.md")
    parser.add_argument(
        "--folder-name",
        type=str,
        default=None,
        help="逻辑目录路径；显式传空串会原样下发",
    )
    parser.add_argument("--project-id", type=int, help="目标项目空间 ID，不传则保存到个人知识库")
    parser.add_argument("--update-file-id", type=int, help="版本更新模式：目标文件 ID")
    parser.add_argument("--version-name", type=str, help="版本名称，如 V2.0")
    parser.add_argument("--version-remark", type=str, help="版本说明")
    parser.add_argument(
        "--name-conflict-strategy",
        type=int,
        choices=[0, 1, 2, 3],
        default=None,
        help="同名冲突策略（若 OpenAPI 支持则下发）；见 references/enums-and-defaults.md",
    )
    add_safety_args(parser)
    args = parser.parse_args()

    file_name, file_suffix = normalize_file_name(args.file_name, args.file_suffix)
    body = {
        "content": args.content,
        "fileName": file_name,
    }
    if file_suffix:
        body["fileSuffix"] = file_suffix
    # P1-2: 用 is not None，空串原样下发
    if args.folder_name is not None:
        body["folderName"] = args.folder_name
    if args.project_id is not None:
        body["projectId"] = args.project_id
    if args.update_file_id is not None:
        body["updateFileId"] = args.update_file_id
    if args.version_name:
        body["versionName"] = args.version_name
    if args.version_remark:
        body["versionRemark"] = args.version_remark
    if args.name_conflict_strategy is not None:
        body["nameConflictStrategy"] = args.name_conflict_strategy

    enforce_or_dry_run(args, method="POST", url=API_PATH, body=body)
    result = call_api(body)
    print(json.dumps(process_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
