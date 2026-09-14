#!/usr/bin/env python3
"""受控批量下载：默认串行；可用 --max-concurrency 限制并发（B-03）。

对每个 fileId 调用 download-file 同路径逻辑（getDownloadInfo → 拉文件）。
并发上限默认 2；超过契约建议值时打印警告。契约正式上限待服务端公布。
"""
import json
import os
import sys
import tempfile
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# 与 download-file 对齐的软契约；正式上限待成伟公布后改此常量并写文档
DEFAULT_MAX_CONCURRENCY = 2
ADVISED_HARD_CAP = 8
API_PATH = "/document-database/file/getDownloadInfo"
CHUNK_SIZE = 1024 * 1024


def _download_one(file_id: int, out_dir: str) -> dict:
    params = [("fileId", str(file_id)), ("forceDownload", "true")]
    url = f"{API_PATH}?{urllib.parse.urlencode(params)}"
    try:
        info = request_open_api(url, method="GET", fatal=False)
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
    safe = os.path.basename(str(name).replace("\\", "/")) or f"{file_id}.bin"
    path = os.path.join(out_dir, f"{file_id}_{safe}")
    import urllib.request

    try:
        req = urllib.request.Request(download_url, method="GET")
        with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as f:
            while True:
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
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
        help="输出目录（默认系统临时目录下 cms-docdb-batch-dl）",
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
    os.makedirs(out_dir, exist_ok=True)

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
            "note": "正式并发上限待服务端契约；本脚本默认 2",
        },
    }
    print(json.dumps(out, ensure_ascii=False))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
