#!/usr/bin/env python3
"""
cms-docdb Open API 公共工具。

鉴权由公共层按固定优先级选择：运行时 AppKey 优先，缺失时使用可选 --app-key。
业务脚本不得手写鉴权头。401 / AUTH_CONTEXT_* 不换 Key 重试。
"""

from __future__ import annotations

import importlib.util
import json
import mimetypes
import os
import re
import ssl
import sys
import time
import uuid
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urljoin
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
)

# 兜底：只读 skill 树禁止写 __pycache__
sys.dont_write_bytecode = True

ParamsType = Union[Mapping[str, Any], Sequence[tuple], None]

RUNTIME_APP_KEY_ENV = "XG_OPENAPI_APP_KEY"
RUNTIME_BASE_URL_ENV = "XG_OPENAPI_BASE_URL"
DEFAULT_BASE_URL = "https://sg-al-cwork-web.mediportal.com.cn/open-api"
MAX_APP_KEY_LENGTH = 256
SHARED_CLIENT_PACKAGE = "xg_openapi_client"

AUTH_MISSING_TEXT = (
    "AUTH_CONTEXT_MISSING: 未获取到企业知识库 AppKey；请提供 AppKey 或完成相关配置后重试"
)
AUTH_INVALID_TEXT = (
    "AUTH_CONTEXT_INVALID: 企业知识库 AppKey 格式非法，不得自动修剪或换用其他来源"
)
AUTH_REDACTED_TEXT = (
    "AUTH_CONTEXT_REDACTED: 企业知识库 AppKey 为脱敏或占位值；"
    "请重新提供原始 AppKey，不得复用历史命令或日志"
)

_REDACTED_PLACEHOLDERS = frozenset(
    {
        "redacted",
        "masked",
        "[redacted_app_key]",
        "<app_key>",
        "<当前用户appkey>",
        "<your_app_key>",
        "<your-app-key>",
    }
)
_REDACTED_STARS_RE = re.compile(r"\*{3,}")
# 文档/命令示例里的尖括号占位（整串形如 <...>，内含 appkey/app_key/app-key 字样）
_REDACTED_ANGLE_PLACEHOLDER_RE = re.compile(
    r"^<[^>]*(?:app[_-]?key|appkey)[^>]*>$",
    re.IGNORECASE,
)

_cli_app_key: Optional[str] = None


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


def stash_cli_app_key(value: Optional[str]) -> None:
    """parse_args 后暂存可选 --app-key；不校验、不选源、不写环境。"""
    global _cli_app_key
    _cli_app_key = value


def reset_auth_state() -> None:
    """测试用：复位 CLI 暂存。不擅自删除进程环境。"""
    global _cli_app_key
    _cli_app_key = None


def mask_app_key(value: str) -> str:
    n = len(value or "")
    if n <= 8:
        return "*" * n
    start = (n - 8) // 2
    return value[:start] + "********" + value[start + 8 :]


def _classify_app_key(value: Optional[str]) -> str:
    if value is None or value == "":
        return "missing"
    if "\n" in value or "\r" in value or "\x00" in value:
        return "invalid"
    if value.strip() != value:
        return "invalid"
    if len(value) > MAX_APP_KEY_LENGTH:
        return "invalid"
    if value.replace("*", "") == "" or _REDACTED_STARS_RE.search(value):
        return "redacted"
    if value.casefold() in _REDACTED_PLACEHOLDERS:
        return "redacted"
    if _REDACTED_ANGLE_PLACEHOLDER_RE.match(value):
        return "redacted"
    return "valid"


def _fail(message: str, exit_code: int = 1) -> None:
    print(message, file=sys.stderr)
    sys.exit(exit_code)


def _log_auth(event: str, source: str, app_key: str, extra: str = "") -> None:
    parts = [
        event,
        f"source={source}",
        f"appKey={mask_app_key(app_key)}",
        f"length={len(app_key)}",
    ]
    if extra:
        parts.append(extra)
    print(" ".join(parts), file=sys.stderr)


def resolve_app_key() -> Tuple[str, str]:
    """
    发业务请求前选源。返回 (app_key, source)。
    source: environment | parameter
    """
    runtime_raw = os.environ.get(RUNTIME_APP_KEY_ENV)
    if runtime_raw is None:
        runtime_kind = "missing"
        runtime_value = None
    else:
        runtime_kind = _classify_app_key(runtime_raw)
        runtime_value = runtime_raw

    cli_kind = _classify_app_key(_cli_app_key)
    cli_present = _cli_app_key is not None and _cli_app_key != ""

    if runtime_kind == "invalid":
        _fail(AUTH_INVALID_TEXT)
    if runtime_kind == "redacted":
        _fail(AUTH_REDACTED_TEXT)
    if runtime_kind == "valid":
        if cli_present:
            _log_auth(
                "OPENAPI_AUTH_SOURCE=environment",
                "environment",
                runtime_value or "",
                "parameter_ignored=true 运行时来源优先，已忽略 --app-key",
            )
        return runtime_value or "", "environment"

    if cli_kind == "invalid":
        _fail(AUTH_INVALID_TEXT)
    if cli_kind == "redacted":
        _fail(AUTH_REDACTED_TEXT)
    if cli_kind == "valid":
        _log_auth(
            "OPENAPI_AUTH_FALLBACK=parameter",
            "parameter",
            _cli_app_key or "",
        )
        os.environ[RUNTIME_APP_KEY_ENV] = _cli_app_key or ""
        return _cli_app_key or "", "parameter"

    _fail(AUTH_MISSING_TEXT)
    raise AssertionError("unreachable")


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


def normalize_base_url(base: Optional[str] = None) -> str:
    raw = (base if base is not None else os.environ.get(RUNTIME_BASE_URL_ENV, "")).strip()
    if not raw:
        raw = DEFAULT_BASE_URL
    raw = raw.rstrip("/")
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    path = parts.path or ""
    lower = path.rstrip("/").lower()
    if lower == "/open-api" or lower.endswith("/open-api"):
        path = path.rstrip("/") or "/open-api"
    else:
        path = (path.rstrip("/") + "/open-api") if path else "/open-api"
    return f"{parts.scheme}://{parts.netloc}{path}"


def _runtime_base_url(client=None) -> str:
    if client is not None:
        for attr in ("base_url", "baseUrl", "open_api_base_url", "_base_url"):
            value = getattr(client, attr, None)
            if isinstance(value, str) and value.strip():
                return normalize_base_url(value)
    return normalize_base_url()


class _SameOriginRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = newurl if "://" in str(newurl) else urljoin(req.full_url, newurl)
        old = urlsplit(req.full_url)
        new = urlsplit(target)
        if (old.scheme, old.netloc.lower()) != (new.scheme, new.netloc.lower()):
            raise URLError("OPENAPI_HTTP_ERROR: 跨源重定向已拒绝，避免携带 AppKey")
        return HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)


class StdlibOpenApiClient:
    """Skill 自带标准库客户端。不提供 upload_file，以便 multipart 走公共层回退。"""

    def __init__(self, app_key: str, base_url: str, timeout: int = 60):
        self.app_key = app_key
        self._app_key = app_key
        self.base_url = normalize_base_url(base_url)
        self.timeout = timeout

    def get(self, path: str, params: ParamsType = None):
        url = self._build_url(path, params)
        return self._request("GET", url)

    def post(self, path: str, body: Any = None):
        url = self._build_url(path, None)
        return self._request("POST", url, body if body is not None else {})

    def put(self, path: str, body: Any = None):
        url = self._build_url(path, None)
        return self._request("PUT", url, body if body is not None else {})

    def _build_url(self, path: str, params: ParamsType) -> str:
        api_path = normalize_open_api_path(path)
        url = self.base_url.rstrip("/") + api_path
        pairs = _params_to_pairs(params)
        if pairs:
            query = urlencode(pairs, doseq=True)
            if query:
                url = f"{url}?{query}"
        return url

    def _request(self, method: str, url: str, body: Any = None) -> dict:
        data = None
        headers = {"appKey": self.app_key}
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            data = payload
            headers["Content-Type"] = "application/json; charset=utf-8"
        req = Request(url, data=data, method=method, headers=headers)
        ctx = ssl.create_default_context()
        opener = build_opener(
            _SameOriginRedirectHandler(),
            HTTPSHandler(context=ctx),
        )
        try:
            with opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read()
                status = getattr(resp, "status", 200)
                return _parse_json_response(status, raw)
        except HTTPError as exc:
            raw = b""
            try:
                raw = exc.read()
            except Exception:
                pass
            if exc.code == 401:
                raise RuntimeError("HTTP 401") from None
            if exc.code == 429 or exc.code >= 500:
                raise RuntimeError(f"OPENAPI_HTTP_ERROR: HTTP {exc.code}") from None
            raise RuntimeError(f"OPENAPI_HTTP_ERROR: HTTP {exc.code}") from None
        except URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            if "跨源重定向" in reason:
                raise RuntimeError(reason) from None
            raise RuntimeError(f"OPENAPI_NETWORK_ERROR: {reason}") from None
        except TimeoutError:
            raise RuntimeError("OPENAPI_NETWORK_ERROR: timeout") from None
        except json.JSONDecodeError:
            raise RuntimeError("OPENAPI_INVALID_RESPONSE: 响应不是有效 JSON") from None


def _parse_json_response(status: int, raw: bytes) -> dict:
    if status == 401:
        raise RuntimeError("HTTP 401")
    text = raw.decode("utf-8", errors="replace") if raw else ""
    if not text.strip():
        if 200 <= status < 300:
            return {"resultCode": 1, "resultMsg": None, "data": None}
        raise RuntimeError(f"OPENAPI_HTTP_ERROR: HTTP {status}")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError("OPENAPI_INVALID_RESPONSE: 响应不是有效 JSON") from None
    if not isinstance(parsed, dict):
        raise RuntimeError("OPENAPI_INVALID_RESPONSE: 响应不是有效 JSON")
    return parsed


def _shared_client_spec_exists() -> bool:
    try:
        return importlib.util.find_spec(SHARED_CLIENT_PACKAGE) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


def get_openapi_client(timeout: int = 60):
    """延迟导入共享客户端；包不存在时使用标准库客户端。"""
    app_key, _source = resolve_app_key()
    if not _shared_client_spec_exists():
        print("OPENAPI_CLIENT_FALLBACK=stdlib", file=sys.stderr)
        return StdlibOpenApiClient(app_key, _runtime_base_url(), timeout=timeout)
    try:
        from xg_openapi_client import OpenApiClient
    except Exception as exc:
        _fail(f"OPENAPI_CLIENT_IMPORT_FAILED: 共享客户端导入失败（{type(exc).__name__}），不自动安装或降级")
    try:
        return OpenApiClient.from_runtime(timeout=timeout)
    except SystemExit:
        raise
    except Exception as exc:
        msg = str(exc)
        if "AUTH_CONTEXT_MISSING" in msg:
            _fail(AUTH_MISSING_TEXT)
        if "AUTH_CONTEXT_INVALID" in msg:
            _fail(AUTH_INVALID_TEXT)
        if "AUTH_CONTEXT_REDACTED" in msg:
            _fail(AUTH_REDACTED_TEXT)
        _fail(f"OPENAPI_CLIENT_INIT_FAILED: 共享客户端初始化失败（{type(exc).__name__}）")
        raise AssertionError("unreachable")



def create_openapi_client(*, timeout: int = 60):
    return get_openapi_client(timeout=timeout)


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
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if item is None:
                        continue
                    pairs.append((str(key), str(item)))
            else:
                pairs.append((str(key), str(value)))
        return pairs
    return [(str(k), str(v)) for k, v in params if v is not None]


def _is_auth_error(exc: BaseException) -> bool:
    """仅识别明确鉴权失败；避免业务文案含「凭证」等词误判。"""
    name = type(exc).__name__
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
        "AUTH_CONTEXT_INVALID",
        "AUTH_CONTEXT_REDACTED",
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
    # 仅对安全读自动重试；写操作状态不明时不得盲重试（避免重复版本/通知/创建）
    max_attempts = 3 if method_u == "GET" else 1
    for attempt in range(max_attempts):
        try:
            if method_u == "GET":
                if params_dict:
                    try:
                        return client.get(path, params=params_dict)
                    except TypeError:
                        q = urlencode(pairs, doseq=True)
                        return client.get(f"{path}?{q}")
                return client.get(path)
            if method_u == "POST":
                payload = body if body is not None else {}
                if params_dict:
                    q = urlencode(pairs, doseq=True)
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
            if attempt < max_attempts - 1:
                time.sleep(1)
                continue
            if method_u != "GET":
                print(
                    f"错误: 写操作失败且未自动重试（避免重复提交）: {e}",
                    file=sys.stderr,
                )
            else:
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


def _runtime_app_key_for_multipart(client) -> str:
    """公共层 multipart 回退：与 JSON 客户端同一选源。"""
    for attr in ("app_key", "appKey", "_app_key"):
        value = getattr(client, attr, None)
        if isinstance(value, str) and _classify_app_key(value) == "valid":
            return value
    app_key, _source = resolve_app_key()
    return app_key


def _is_same_origin(scheme: str, host: str, target: str) -> bool:
    parsed = urlsplit(target)
    new_scheme = parsed.scheme or scheme
    new_host = parsed.netloc or host
    return (new_scheme, new_host.lower()) == (scheme, host.lower())


def upload_multipart_file(
    path: str,
    file_path: str,
    *,
    field_name: str = "file",
    timeout: int = 120,
    max_retries: int = 1,
) -> dict:
    """
    上传本地文件（multipart）。优先客户端 upload/post_multipart；
    否则由公共层用选定 AppKey 发请求（业务脚本不得手写鉴权头）。
    """
    client = get_openapi_client(timeout=timeout)
    api_path = normalize_open_api_path(path)

    if hasattr(client, "upload_file"):
        return client.upload_file(api_path, file_path, field_name=field_name)
    if hasattr(client, "post_multipart"):
        with open(file_path, "rb") as fh:
            return client.post_multipart(api_path, files={field_name: fh})

    import http.client

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
                            raise RuntimeError(f"OPENAPI_HTTP_ERROR: HTTP {status} 重定向缺少 Location")
                        target = urljoin(f"{cur_scheme}://{cur_host}{cur_path}", location)
                        if not _is_same_origin(cur_scheme, cur_host, target):
                            raise RuntimeError("OPENAPI_HTTP_ERROR: 跨源重定向已拒绝，避免携带 AppKey")
                        p = urlsplit(target)
                        cur_scheme = p.scheme or cur_scheme
                        cur_host = p.netloc or cur_host
                        cur_path = p.path or "/"
                        if p.query:
                            cur_path = f"{cur_path}?{p.query}"
                        continue
                    text = body.decode("utf-8", errors="replace")
                    if status == 401:
                        print("错误: HTTP 401", file=sys.stderr)
                        sys.exit(1)
                    if status == 429 or status >= 500:
                        raise RuntimeError(f"OPENAPI_HTTP_ERROR: HTTP {status}")
                    if status >= 400:
                        raise RuntimeError(f"OPENAPI_HTTP_ERROR: HTTP {status}")
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        raise RuntimeError("OPENAPI_INVALID_RESPONSE: 响应不是有效 JSON") from None
                finally:
                    conn.close()
            raise RuntimeError("OPENAPI_HTTP_ERROR: 重定向次数过多")
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
    自动去掉 host 与 /open-api 前缀，走统一客户端工厂。
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
