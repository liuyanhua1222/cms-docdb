#!/usr/bin/env python3
"""
cms-docdb Open API 公共工具（appKey 鉴权、getFileBasicInfo、projectId 解析、TLS）
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Optional

OPEN_API_BASE = "https://sg-al-cwork-web.mediportal.com.cn/open-api/document-database"


def ensure_common_on_path(caller_file: str) -> str:
    """
    将 scripts/common 加入 sys.path。
    - scripts/<module>/*.py → ../common
    - scripts/*.py → ./common
    返回 common 绝对路径。
    """
    here = os.path.dirname(os.path.abspath(caller_file))
    candidates = [
        os.path.join(here, "common"),
        os.path.join(here, "..", "common"),
        here if os.path.basename(here) == "common" else "",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        common = os.path.abspath(candidate)
        if os.path.isdir(common) and os.path.isfile(os.path.join(common, "docdb_open_api.py")):
            if common not in sys.path:
                sys.path.insert(0, common)
            return common
    raise RuntimeError(f"无法定位 scripts/common（caller={caller_file}）")


def app_key_headers(extra: Optional[Dict] = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if extra:
        headers.update(extra)
    app_key = os.environ.get("appkey")
    if not app_key:
        print("错误: 未找到 appkey，请确认小龙虾运行时上下文已注入 appkey", file=sys.stderr)
        sys.exit(1)
    headers["appKey"] = app_key
    return headers


def ssl_context() -> ssl.SSLContext:
    """默认启用 TLS 校验；仅 CMS_DOCDB_INSECURE_SSL=1 时临时关闭（排障用）。"""
    ctx = ssl.create_default_context()
    if os.environ.get("CMS_DOCDB_INSECURE_SSL") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_json(url: str, method: str = "GET", body: Optional[dict] = None, timeout: int = 60) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=app_key_headers(), method=method)
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        print(f"错误: HTTP {e.code} - {e.reason} {err_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def get_file_basic_info(file_id: int) -> dict:
    """调用 1.17 getFileBasicInfo，返回 data 对象。"""
    url = f"{OPEN_API_BASE}/file/getFileBasicInfo?{urllib.parse.urlencode({'fileId': str(file_id)})}"
    result = fetch_json(url)
    if result.get("resultCode") != 1:
        print(f"错误: getFileBasicInfo 失败 - {result.get('resultMsg')}", file=sys.stderr)
        sys.exit(1)
    data = result.get("data")
    if not isinstance(data, dict):
        print("错误: getFileBasicInfo 响应 data 无效", file=sys.stderr)
        sys.exit(1)
    return data


def resolve_project_id_for_parent(parent_id: int, fallback_project_id: Optional[int] = None) -> int:
    """
    parentId != 0 时通过 getFileBasicInfo 反查 projectId；
    parentId == 0 时必须提供 fallback_project_id（空间根上传）。
    """
    if parent_id == 0:
        if fallback_project_id is None:
            print("错误: parentId=0 时必须显式提供 projectId", file=sys.stderr)
            sys.exit(1)
        return fallback_project_id

    data = get_file_basic_info(parent_id)
    resolved = data.get("projectId")
    if resolved is None:
        print(f"错误: 无法从 parentId={parent_id} 解析 projectId", file=sys.stderr)
        sys.exit(1)
    resolved = int(resolved)

    if fallback_project_id is not None and int(fallback_project_id) != resolved:
        print(
            f"提示: 传入 projectId={fallback_project_id} 与父目录实际 projectId={resolved} 不一致，"
            f"已自动使用 {resolved}（与 dev-guide 工作流 A7 一致）",
            file=sys.stderr,
        )
    return resolved
