#!/usr/bin/env python3
"""
cms-docdb Open API 公共工具。

鉴权由运行时通过 OpenApiClient.from_runtime() 注入；本模块不接受 --appkey，
不从会话上下文或配置文件查找默认凭证。401 / AUTH_CONTEXT_MISSING 不换 Key 重试。
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import uuid
from typing import Any, Dict, Mapping, Optional, Sequence, Union
from urllib.parse import urlencode, urlsplit, urljoin

# 兜底：只读 skill 树禁止写 __pycache__
sys.dont_write_bytecode = True

ParamsType = Union[Mapping[str, Any], Sequence[tuple], None]


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


def normalize_open_api_path(path: str) -> str:
    """相对 /open-api 根的路径；去掉重复的 /open-api 前缀与 host。"""
    raw = (path or "").strip()
    if not raw:
        raise ValueError("OpenAPI path 不能为空")
    if "://" in raw:
        parts = urlsplit(raw)
        raw = parts.path or "/"
        if parts.query:
            raw = f"{raw}?{parts.query}"
    if not raw.startswith("/"):
        raw = "/" + raw
    lower = raw.lower()
    if lower.startswith("/open-api/"):
        raw = raw[len("/open-api") :]
    elif lower == "/open-api":
        raw = "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    return raw


def get_openapi_client(timeout: int = 60):
    """创建运行时客户端；缺凭证时由客户端抛出 AUTH_CONTEXT_MISSING 等公开错误。"""
    try:
        from xg_openapi_client import OpenApiClient
    except ImportError:
        print(
            "错误: 未安装 xg_openapi_client。\n"
            "该依赖由 Sandbox 镜像提供；请勿在 Skill 内 pip 安装或回退到手工鉴权。",
            file=sys.stderr,
        )
        sys.exit(1)
    return OpenApiClient.from_runtime(timeout=timeout)


def _params_to_pairs(params: ParamsType) -> list:
    if params is None:
        return []
    if isinstance(params, Mapping):
        pairs = []
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                pairs.append((str(key), "true" if value else "false"))
            else:
                pairs.append((str(key), str(value)))
        return pairs
    return [(str(k), str(v)) for k, v in params if v is not None]


def _is_auth_error(exc: BaseException) -> bool:
    """仅识别明确鉴权失败；避免业务文案含「凭证」等词误判。"""
    name = type(exc).__name__
    # 不含 PermissionError：避免本地文件权限异常被误判为鉴权失败
    if name in {"AuthenticationError", "AuthError", "Unauthorized"}:
        return True
    code = getattr(exc, "status_code", None) or getattr(exc, "status", None) or getattr(exc, "code", None)
    try:
        if int(code) == 401:
            return True
    except (TypeError, ValueError):
        pass
    msg = str(exc)
    markers = (
        "AUTH_CONTEXT_MISSING",
        "HTTP 401",
        "status=401",
        "status code 401",
        "Unauthorized",
    )
    return any(m in msg for m in markers)


def _call_client(method: str, path: str, *, params: ParamsType = None, body: Any = None, timeout: int = 60):
    """
    按 xg-openapi-client 约定调用：
      client.get(path) / client.get(path, params=...)
      client.post(path, body)
    path 已相对 /open-api 根；query 用 params，不塞进 path（除非 client 不支持 params）。
    """
    client = get_openapi_client(timeout=timeout)
    path = normalize_open_api_path(path)
    method_u = method.upper()
    pairs = _params_to_pairs(params)
    params_dict = dict(pairs) if pairs else None

    last_error: Optional[BaseException] = None
    for attempt in range(3):
        try:
            if method_u == "GET":
                if params_dict:
                    try:
                        return client.get(path, params=params_dict)
                    except TypeError:
                        q = urlencode(pairs)
                        return client.get(f"{path}?{q}")
                return client.get(path)
            if method_u == "POST":
                payload = body if body is not None else {}
                if params_dict:
                    q = urlencode(pairs)
                    post_path = f"{path}?{q}"
                else:
                    post_path = path
                return client.post(post_path, payload)
            if method_u == "PUT":
                payload = body if body is not None else {}
                return client.put(path, payload)
            raise RuntimeError(f"OpenApiClient 不支持方法 {method_u}")
        except SystemExit:
            raise
        except Exception as e:
            last_error = e
            if _is_auth_error(e):
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)
            if attempt < 2:
                time.sleep(1)
                continue
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    print(f"错误: {last_error}", file=sys.stderr)
    sys.exit(1)


def api_get(path: str, params: ParamsType = None, timeout: int = 60) -> dict:
    """GET 相对 /open-api 根的 path。"""
    return _call_client("GET", path, params=params, timeout=timeout)


def api_post(path: str, body: Any = None, params: ParamsType = None, timeout: int = 60) -> dict:
    """POST JSON；path 相对 /open-api 根。"""
    return _call_client("POST", path, params=params, body=body, timeout=timeout)


def api_put(path: str, body: Any = None, params: ParamsType = None, timeout: int = 60) -> dict:
    """PUT JSON；path 相对 /open-api 根。"""
    return _call_client("PUT", path, params=params, body=body, timeout=timeout)


def _runtime_base_url(client) -> str:
    for attr in ("base_url", "baseUrl", "open_api_base_url", "_base_url"):
        value = getattr(client, attr, None)
        if isinstance(value, str) and value.strip():
            return value.rstrip("/")
    env = os.environ.get("XG_OPENAPI_BASE_URL", "").strip().rstrip("/")
    if env:
        return env
    # 与 xg-openapi-client 默认生产地址一致；保证 /open-api 只出现一次
    return "https://sg-al-cwork-web.mediportal.com.cn/open-api"


def _runtime_app_key_for_multipart(client) -> str:
    """
    仅供公共层 multipart 回退使用。
    优先客户端属性；否则读插件注入的进程环境（与 from_runtime 同源）。
    禁止业务脚本直接调用或接受 CLI --appkey。
    """
    for attr in ("app_key", "appKey", "_app_key"):
        value = getattr(client, attr, None)
        if isinstance(value, str) and value.strip():
            return value
    value = os.environ.get("XG_OPENAPI_APP_KEY", "").strip()
    if value:
        return value
    print(
        "错误: AUTH_CONTEXT_MISSING — 当前工具子进程未注入 OpenAPI 凭证。\n"
        "请向用户展示该公开错误；禁止询问、拼接或更换密钥。",
        file=sys.stderr,
    )
    sys.exit(1)


def upload_multipart_file(
    path: str,
    file_path: str,
    *,
    field_name: str = "file",
    timeout: int = 120,
    max_retries: int = 3,
) -> dict:
    """
    上传本地文件（multipart）。优先客户端 upload/post_multipart；
    否则由公共层用运行时注入的凭证发请求（业务脚本不得手写鉴权头）。
    """
    client = get_openapi_client(timeout=timeout)
    api_path = normalize_open_api_path(path)

    if hasattr(client, "upload_file"):
        return client.upload_file(api_path, file_path, field_name=field_name)
    if hasattr(client, "post_multipart"):
        with open(file_path, "rb") as fh:
            return client.post_multipart(api_path, files={field_name: fh})

    # 公共层回退：不经过业务脚本写 appKey
    import http.client
    import ssl

    app_key = _runtime_app_key_for_multipart(client)
    base = _runtime_base_url(client)
    parsed = urlsplit(base if "://" in base else f"https://{base}")
    scheme = parsed.scheme or "https"
    host = parsed.netloc
    base_path = (parsed.path or "").rstrip("/")
    request_path = f"{base_path}{api_path}"

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    boundary = uuid.uuid4().hex
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    content_length = len(header) + file_size + len(footer)
    chunk_size = 5 * 1024 * 1024
    backoff = (1, 2, 4)

    ctx = ssl.create_default_context()
    if os.environ.get("CMS_DOCDB_INSECURE_SSL") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    last_error: Optional[BaseException] = None
    for attempt in range(max_retries):
        try:
            cur_scheme, cur_host, cur_path = scheme, host, request_path
            for _ in range(6):
                if cur_scheme == "http":
                    conn = http.client.HTTPConnection(cur_host, timeout=timeout)
                else:
                    conn = http.client.HTTPSConnection(cur_host, timeout=timeout, context=ctx)
                try:
                    conn.putrequest("POST", cur_path)
                    conn.putheader("appKey", app_key)
                    conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
                    conn.putheader("Content-Length", str(content_length))
                    conn.endheaders()
                    conn.send(header)
                    with open(file_path, "rb") as fh:
                        while True:
                            chunk = fh.read(chunk_size)
                            if not chunk:
                                break
                            conn.send(chunk)
                    conn.send(footer)
                    resp = conn.getresponse()
                    status = resp.status
                    body = resp.read()
                    if status in (301, 302, 303, 307, 308):
                        location = resp.getheader("Location")
                        resp.close()
                        if not location:
                            raise RuntimeError(f"HTTP {status} 重定向缺少 Location")
                        target = urljoin(f"{cur_scheme}://{cur_host}{cur_path}", location)
                        p = urlsplit(target)
                        cur_scheme = p.scheme or cur_scheme
                        cur_host = p.netloc or cur_host
                        cur_path = p.path or "/"
                        if p.query:
                            cur_path = f"{cur_path}?{p.query}"
                        continue
                    text = body.decode("utf-8", errors="replace")
                    if status == 401:
                        print(f"错误: HTTP 401 鉴权失败 {text[:500]}", file=sys.stderr)
                        sys.exit(1)
                    if status == 429 or status >= 500:
                        raise RuntimeError(f"HTTP {status} - {text[:500]}")
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {
                            "resultCode": 0,
                            "resultMsg": f"HTTP {status} 返回非 JSON 响应: {text[:500]}",
                            "data": None,
                        }
                finally:
                    conn.close()
            raise RuntimeError("重定向次数过多")
        except Exception as e:
            last_error = e
            if _is_auth_error(e):
                print(f"错误: {e}", file=sys.stderr)
                sys.exit(1)
            if attempt < max_retries - 1:
                time.sleep(backoff[min(attempt, len(backoff) - 1)])
                continue
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    print(f"错误: {last_error}", file=sys.stderr)
    sys.exit(1)


def get_file_basic_info(file_id: int) -> dict:
    """调用 getFileBasicInfo，返回 data 对象。"""
    result = api_get(
        "/document-database/file/getFileBasicInfo",
        params={"fileId": str(file_id)},
    )
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
            f"已自动使用 {resolved}",
            file=sys.stderr,
        )
    return resolved


def request_open_api(
    url_or_path: str,
    method: str = "GET",
    body: Any = None,
    timeout: int = 60,
    params: ParamsType = None,
) -> dict:
    """
    兼容旧脚本：接受完整 URL 或相对 path。
    自动去掉 host 与 /open-api 前缀，走 OpenApiClient.from_runtime()。
    """
    raw = (url_or_path or "").strip()
    query_pairs: list = list(_params_to_pairs(params))
    if "://" in raw or raw.startswith("/"):
        parts = urlsplit(raw if "://" in raw else f"https://dummy.local{raw}")
        path = parts.path or "/"
        if parts.query:
            from urllib.parse import parse_qsl

            query_pairs.extend(parse_qsl(parts.query, keep_blank_values=True))
        path = normalize_open_api_path(path)
    else:
        path = normalize_open_api_path(raw)
    return _call_client(method, path, params=query_pairs or None, body=body, timeout=timeout)
