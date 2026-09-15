#!/usr/bin/env python3
"""受控批量下载：默认串行；可用 --max-concurrency 限制并发（B-03）。

对每个 fileId 复用 download-file 的安全落盘（拒 symlink、.part 原子替换、默认不覆盖）。
并发上限默认 2；超过契约建议值时打印警告。契约正式上限待服务端公布。
"""
import importlib.util
import json
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

_cms_here = os.path.dirname(os.path.abspath(__file__))
_cms_common = os.path.join(_cms_here, "common")
if not os.path.isfile(os.path.join(_cms_common, "docdb_open_api.py")):
    _cms_common = os.path.join(_cms_here, "..", "common")
_cms_common = os.path.abspath(_cms_common)
if _cms_common not in sys.path:
    sys.path.insert(0, _cms_common)
sys.dont_write_bytecode = True
from docdb_open_api import ensure_common_on_path

ensure_common_on_path(__file__)
from cli_args import DocdbArgumentParser

# 与 download-file 对齐的软契约；正式上限待成伟公布后改此常量并写文档
DEFAULT_MAX_CONCURRENCY = 2
ADVISED_HARD_CAP = 8


def _load_download_file_module():
    path = os.path.join(_cms_here, "download-file.py")
    spec = importlib.util.spec_from_file_location("cms_docdb_download_file", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_dl = _load_download_file_module()


def _ensure_out_dir_in_jail(out_dir: str) -> str:
    """输出目录须在下载沙箱内；自定义目录时临时扩展 CMS_DOCDB_DOWNLOAD_DIR。"""
    abs_out = os.path.abspath(out_dir)
    # 先拒 symlink，再 mkdir，避免 makedirs(exist_ok) 跟随链接落到沙箱外
    if os.path.lexists(abs_out) and os.path.islink(abs_out):
        raise RuntimeError("输出目录为符号链接，拒绝写入")
    roots = _dl._download_jail_roots()
    probe = os.path.join(abs_out, ".batch-probe")
    if not _dl._is_under_jail(probe, roots):
        # 允许用户显式指定的批量输出根进入沙箱（与单文件 CMS_DOCDB_DOWNLOAD_DIR 同语义）
        os.environ["CMS_DOCDB_DOWNLOAD_DIR"] = abs_out
        roots = _dl._download_jail_roots()
        if not _dl._is_under_jail(probe, roots):
            raise RuntimeError(
                "输出目录越出下载沙箱；请使用系统临时目录，或设置 CMS_DOCDB_DOWNLOAD_DIR"
            )
    os.makedirs(abs_out, exist_ok=True)
    if os.path.islink(abs_out):
        raise RuntimeError("输出目录为符号链接，拒绝写入")
    return abs_out


def _download_one(file_id: int, out_dir: str) -> dict:
    try:
        info = _dl.get_download_url(file_id)
    except Exception as e:
        return {"fileId": file_id, "ok": False, "error": str(e)}
    if not isinstance(info, dict) or info.get("resultCode") != 1:
        return {
            "fileId": file_id,
            "ok": False,
            "error": (info or {}).get("resultMsg") if isinstance(info, dict) else "getDownloadInfo failed",
        }
    data = info.get("data") or {}
    download_url = data.get("downloadUrl") or data.get("url")
    name = data.get("fileName") or data.get("name") or f"{file_id}.bin"
    if not download_url:
        return {"fileId": file_id, "ok": False, "error": "missing downloadUrl"}
    safe = _dl.sanitize_download_basename(str(name))
    # 相对 out_dir 的文件名；resolve_output_path 负责沙箱与目录创建
    rel = os.path.join(out_dir, f"{file_id}_{safe}")
    try:
        path = _dl.resolve_output_path(rel, safe)
        _dl.download_file_to_path(download_url, path, force_overwrite=False)
    except Exception as e:
        return {"fileId": file_id, "ok": False, "error": str(e)}
    return {"fileId": file_id, "ok": True, "path": path}


def main():
    p = DocdbArgumentParser(
        hint="""batch-download-files.py 必须提供 --file-ids。
默认并发 2（B-03 受控下载）；勿一次开到 36。
示例: python3 -B <skill-dir>/scripts/query/batch-download-files.py --file-ids "1,2,3"
"""
    )
    p.add_argument("--file-ids", required=True, help="逗号分隔 fileId")
    p.add_argument(
        "--max-concurrency",
        type=int,
        default=DEFAULT_MAX_CONCURRENCY,
        help=f"最大并发，默认 {DEFAULT_MAX_CONCURRENCY}；建议不超过 {ADVISED_HARD_CAP}",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="输出目录（默认系统临时目录下 cms-docdb-batch-dl；须在下载沙箱内）",
    )
    args = p.parse_args()
    ids = [int(x.strip()) for x in args.file_ids.split(",") if x.strip()]
    if not ids:
        print("错误: --file-ids 不能为空", file=sys.stderr)
        sys.exit(1)
    conc = max(1, int(args.max_concurrency))
    if conc > ADVISED_HARD_CAP:
        print(
            f"警告: max-concurrency={conc} 超过建议硬顶 {ADVISED_HARD_CAP}，仍继续；"
            "生产批量归档请等待正式契约上限",
            file=sys.stderr,
        )
    out_dir = args.output_dir or os.path.join(tempfile.gettempdir(), "cms-docdb-batch-dl")
    try:
        out_dir = _ensure_out_dir_in_jail(out_dir)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(2)

    results = []
    failed = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=conc) as pool:
        futs = {pool.submit(_download_one, fid, out_dir): fid for fid in ids}
        for fut in as_completed(futs):
            row = fut.result()
            results.append(row)
            if not row.get("ok"):
                failed.append(row.get("fileId"))

    out = {
        "resultCode": 1 if not failed else 0,
        "resultMsg": None if not failed else f"部分失败 fileIds={failed}",
        "data": {
            "maxConcurrency": conc,
            "outputDir": out_dir,
            "elapsedMs": int((time.time() - t0) * 1000),
            "results": results,
            "failedFileIds": failed,
            "note": "正式并发上限待服务端契约；本脚本默认 2；落盘复用 download-file 安全写",
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
