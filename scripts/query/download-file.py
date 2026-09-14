#!/usr/bin/env python3
"""
query / downloadFile 脚本

用途：下载文件到本地（先获取下载链接，再下载文件）

使用方式：
  python3 -B <skill-dir>/scripts/query/download-file.py --file-id 12345

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
CHUNK_SIZE = 1024 * 1024
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (1, 2, 4)
MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024  # 512MB 软上限


def _download_jail_roots() -> list:
    """返回 realpath 后的沙箱根，避免 /tmp 与 /private/tmp 等符号链接不一致。"""
    raw_roots = [tempfile.gettempdir()]
    extra = (os.environ.get("CMS_DOCDB_DOWNLOAD_DIR") or "").strip()
    if extra:
        raw_roots.append(extra)
    roots = []
    for r in raw_roots:
        roots.append(os.path.realpath(os.path.abspath(r)))
    return roots


def _is_under_jail(path: str, roots: list) -> bool:
    """用父目录 realpath 防「临时目录内 symlink 指到沙箱外」。"""
    abs_path = os.path.abspath(path)
    parent = os.path.dirname(abs_path) or abs_path
    try:
        real_parent = os.path.realpath(parent)
    except OSError:
        real_parent = os.path.abspath(parent)
    candidate = os.path.join(real_parent, os.path.basename(abs_path))
    for root in roots:
        try:
            if os.path.commonpath([candidate, root]) == root:
                return True
        except ValueError:
            continue
    return False


def _reject_existing_symlink(path: str) -> None:
    """拒绝最终输出文件为符号链接，避免 open(..., wb) 跟随链接越界写入。"""
    try:
        if os.path.lexists(path) and os.path.islink(path):
            print("错误: 输出文件为符号链接，拒绝覆盖", file=sys.stderr)
            sys.exit(2)
    except OSError as e:
        print(f"错误: 无法检查输出文件: {e}", file=sys.stderr)
        sys.exit(2)


def sanitize_download_basename(name: str) -> str:
    base = os.path.basename((name or "").replace("\\", "/").strip()) or "download.bin"
    base = base.replace("\x00", "")
    if base in (".", "..") or "/" in base or "\\" in base:
        base = "download.bin"
    base = "".join(ch for ch in base if ord(ch) >= 32)
    return base[:180] or "download.bin"


def resolve_output_path(output: str, file_name: str) -> str:
    """输出必须落在系统临时目录，或 CMS_DOCDB_DOWNLOAD_DIR 指定根下。"""
    safe_name = sanitize_download_basename(file_name)
    roots = _download_jail_roots()
    default_root = roots[0]
    if not output:
        path = os.path.join(default_root, safe_name)
    else:
        out = output
        if not os.path.isabs(out):
            out = os.path.join(default_root, out)
        out = os.path.abspath(out)
        if out.endswith(os.sep) or os.path.isdir(out):
            path = os.path.join(out, safe_name)
        else:
            parent = os.path.dirname(out) or default_root
            path = os.path.join(os.path.abspath(parent), sanitize_download_basename(os.path.basename(out)))
    path = os.path.abspath(path)
    _reject_existing_symlink(path)
    if not _is_under_jail(path, roots):
        print(
            "错误: 输出路径越出下载沙箱；默认仅允许系统临时目录。"
            "若需其它目录请设置 CMS_DOCDB_DOWNLOAD_DIR 为允许根路径。",
            file=sys.stderr,
        )
        sys.exit(2)
    _reject_existing_symlink(path)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError as e:
            print(f"错误: 无法创建输出目录 - {e}", file=sys.stderr)
            sys.exit(2)
    # 创建目录后再用 realpath 复核，防止 mkdir 过程中被换成 symlink
    if not _is_under_jail(path, roots):
        print("错误: 输出目录 realpath 越出下载沙箱", file=sys.stderr)
        sys.exit(2)
    return path


def get_download_url(file_id: int) -> dict:
    """获取文件下载链接"""
    params = [("fileId", str(file_id)), ("forceDownload", "true")]
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"

    return request_open_api(url, method="GET")

def download_file(download_url: str, output_path: str, *, force_overwrite: bool = False) -> str:
    """下载已签发 URL。每次重试写入独立临时文件，成功后原子替换目标。"""
    import urllib.request
    import uuid
    _reject_existing_symlink(output_path)
    if os.path.lexists(output_path) and not force_overwrite:
        print("错误: 输出文件已存在；默认不覆盖。若确认覆盖请传 --force-overwrite", file=sys.stderr)
        sys.exit(2)
    parent = os.path.dirname(output_path) or tempfile.gettempdir()
    if os.path.islink(parent):
        print("错误: 输出父目录为符号链接，拒绝写入", file=sys.stderr)
        sys.exit(2)
    for attempt in range(MAX_RETRIES):
        partial = os.path.join(parent, f".{os.path.basename(output_path)}.{uuid.uuid4().hex}.part")
        try:
            req = urllib.request.Request(download_url, method="GET")
            written = 0
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(partial, flags, 0o600)
            try:
                with urllib.request.urlopen(req, timeout=120) as resp, os.fdopen(fd, "wb") as f:
                    fd = -1  # fdopen 接管
                    while True:
                        chunk = resp.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > MAX_DOWNLOAD_BYTES:
                            raise RuntimeError(f"下载超过大小上限 {MAX_DOWNLOAD_BYTES} 字节")
                        f.write(chunk)
            finally:
                if fd >= 0:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            _reject_existing_symlink(output_path)
            if os.path.lexists(output_path) and not force_overwrite:
                raise RuntimeError("目标文件在下载期间已出现，拒绝覆盖")
            os.replace(partial, output_path)
            return output_path
        except Exception as e:
            try:
                if os.path.lexists(partial):
                    os.unlink(partial)
            except OSError:
                pass
            if attempt < MAX_RETRIES - 1 and "超过大小上限" not in str(e) and "拒绝覆盖" not in str(e):
                time.sleep(RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)])
            else:
                print(f"错误: 下载失败 - {e}", file=sys.stderr)
                sys.exit(1)

def main():
    parser = DocdbArgumentParser(description="下载文件到本地", hint="""download-file.py 必须提供 --file-id。
优先省略 --output（默认写系统临时目录，读 stdout 路径）；禁止 shell 重定向。
示例: python3 -B <skill-dir>/scripts/query/download-file.py --file-id 12345；缺参补齐后用同一 python 命令重试
""",
    )
    parser.add_argument("--file-id", dest="file_id", required=True, type=int, help="文件 ID")
    parser.add_argument(
        "--output",
        type=str,
        help="输出路径（相对路径相对临时目录；绝对路径须在临时目录或 CMS_DOCDB_DOWNLOAD_DIR 下）",
    )
    parser.add_argument(
        "--force-overwrite",
        action="store_true",
        help="允许覆盖已存在的普通文件（仍拒绝符号链接）",
    )
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
    file_name = sanitize_download_basename(data.get('fileName', f'file_{args.file_id}'))
    
    if not download_url:
        print(json.dumps({
            'resultCode': 0,
            'resultMsg': '未获取到下载链接',
            'data': None
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 2. 确定输出路径（净化 basename + 目录边界）
    output_path = resolve_output_path(args.output, file_name)
    
    # 3. 下载文件
    saved_path = download_file(download_url, output_path, force_overwrite=args.force_overwrite)
    
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
