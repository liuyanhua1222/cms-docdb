#!/usr/bin/env python3
"""cms-docdb AppKey 双来源与标准库客户端回归。"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

SKILL_ROOT = Path(__file__).resolve().parents[1]
COMMON = SKILL_ROOT / "scripts" / "common"
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(COMMON))

import cli_args  # noqa: E402
import docdb_open_api as api  # noqa: E402


RUNTIME_ENV = "XG_OPENAPI_APP_KEY"
RUNTIME_KEY = "runtimeAB12345678"
PARAM_KEY = "paramXYZ12345678"


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self._had_runtime = RUNTIME_ENV in os.environ
        self._old_runtime = os.environ.get(RUNTIME_ENV)
        os.environ.pop(RUNTIME_ENV, None)
        api.reset_auth_state()

    def tearDown(self):
        api.reset_auth_state()
        if self._had_runtime:
            os.environ[RUNTIME_ENV] = self._old_runtime or ""
        else:
            os.environ.pop(RUNTIME_ENV, None)

    def _stderr_resolve(self, fn):
        buf = io.StringIO()
        with redirect_stderr(buf):
            try:
                result = fn()
            except SystemExit as exc:
                return exc.code, buf.getvalue(), None
        return 0, buf.getvalue(), result


class TestHelp(AuthTestCase):
    def test_all_docdb_parsers_show_optional_app_key(self):
        scripts = []
        for path in SCRIPTS.rglob("*.py"):
            if path.name in {"docdb_open_api.py", "cli_args.py", "safety.py"}:
                continue
            text = path.read_text(encoding="utf-8")
            if "DocdbArgumentParser" in text:
                scripts.append(path)
        self.assertGreaterEqual(len(scripts), 40)
        missing = []
        for path in scripts:
            proc = subprocess.run(
                [sys.executable, "-B", str(path), "--help"],
                capture_output=True,
                text=True,
                cwd=str(SKILL_ROOT),
            )
            help_text = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0 or "--app-key" not in help_text or "APP_KEY" not in help_text:
                missing.append((str(path.relative_to(SKILL_ROOT)), proc.returncode, help_text[-400:]))
        self.assertEqual(missing, [])

    def test_import_and_help_without_shared_client(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "browse" / "get-app-list.py"), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--app-key", proc.stdout)


class TestSourcePriority(AuthTestCase):
    def test_runtime_wins_parameter_ignored(self):
        os.environ[RUNTIME_ENV] = RUNTIME_KEY
        api.stash_cli_app_key(PARAM_KEY)
        code, err, result = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 0)
        self.assertEqual(result[0], RUNTIME_KEY)
        self.assertEqual(result[1], "environment")
        self.assertIn("OPENAPI_AUTH_SOURCE=environment", err)
        self.assertIn("parameter_ignored=true", err)
        self.assertIn("********", err)
        self.assertNotIn(RUNTIME_KEY, err)
        self.assertNotIn(PARAM_KEY, err)

    def test_parameter_fallback_when_runtime_missing(self):
        api.stash_cli_app_key(PARAM_KEY)
        code, err, result = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 0)
        self.assertEqual(result[0], PARAM_KEY)
        self.assertEqual(result[1], "parameter")
        self.assertIn("OPENAPI_AUTH_FALLBACK=parameter", err)
        self.assertEqual(os.environ.get(RUNTIME_ENV), PARAM_KEY)
        self.assertNotIn(PARAM_KEY, err)

    def test_both_missing(self):
        code, err, _ = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 1)
        self.assertIn("AUTH_CONTEXT_MISSING", err)
        self.assertIn("企业知识库 AppKey", err)

    def test_invalid_runtime_not_overridden(self):
        os.environ[RUNTIME_ENV] = "  " + RUNTIME_KEY + "  "
        api.stash_cli_app_key(PARAM_KEY)
        code, err, _ = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 1)
        self.assertIn("AUTH_CONTEXT_INVALID", err)

    def test_spaces_only_invalid(self):
        api.stash_cli_app_key("     ")
        code, err, _ = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 1)
        self.assertIn("AUTH_CONTEXT_INVALID", err)

    def test_empty_runtime_uses_parameter(self):
        os.environ[RUNTIME_ENV] = ""
        api.stash_cli_app_key(PARAM_KEY)
        code, err, result = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 0)
        self.assertEqual(result[1], "parameter")
        self.assertIn("OPENAPI_AUTH_FALLBACK=parameter", err)

    def test_parse_args_does_not_select_source(self):
        parser = cli_args.DocdbArgumentParser(prog="t")
        ns = parser.parse_args(["--app-key", PARAM_KEY])
        self.assertEqual(ns.app_key, PARAM_KEY)
        self.assertNotIn(RUNTIME_ENV, os.environ)

    def test_dry_run_without_app_key(self):
        script = SCRIPTS / "delete" / "delete-file.py"
        env = os.environ.copy()
        env.pop(RUNTIME_ENV, None)
        proc = subprocess.run(
            [sys.executable, "-B", str(script), "12345", "--dry-run"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload.get("dryRun"))


class TestRedactedMatrix(AuthTestCase):
    def test_classify_redacted_forms(self):
        self.assertEqual(api._classify_app_key("***"), "redacted")
        self.assertEqual(api._classify_app_key("********"), "redacted")
        self.assertEqual(api._classify_app_key("abc***def"), "redacted")
        self.assertEqual(api._classify_app_key("REDACTED"), "redacted")
        self.assertEqual(api._classify_app_key("masked"), "redacted")
        self.assertEqual(api._classify_app_key("[REDACTED_APP_KEY]"), "redacted")
        self.assertEqual(api._classify_app_key("<APP_KEY>"), "redacted")
        self.assertEqual(api._classify_app_key("<当前用户AppKey>"), "redacted")
        self.assertEqual(api._classify_app_key("<your-app-key>"), "redacted")
        self.assertEqual(api._classify_app_key(PARAM_KEY), "valid")

    def test_runtime_redacted_not_overridden_by_valid_param(self):
        os.environ[RUNTIME_ENV] = "***"
        api.stash_cli_app_key(PARAM_KEY)
        code, err, _ = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 1)
        self.assertIn("AUTH_CONTEXT_REDACTED", err)
        self.assertNotIn(PARAM_KEY, err)

    def test_param_redacted_when_runtime_missing(self):
        for value in ("***", "REDACTED", "<APP_KEY>", "<当前用户AppKey>"):
            with self.subTest(value=value):
                api.reset_auth_state()
                api.stash_cli_app_key(value)
                code, err, _ = self._stderr_resolve(api.resolve_app_key)
                self.assertEqual(code, 1)
                self.assertIn("AUTH_CONTEXT_REDACTED", err)
                # 错误文案不得回显候选原值（REDACTED 可能出现在错误码中，需剔除后再比）
                residual = err.replace("AUTH_CONTEXT_REDACTED", "")
                self.assertNotIn(value, residual)

    def test_runtime_valid_ignores_redacted_param(self):
        os.environ[RUNTIME_ENV] = RUNTIME_KEY
        api.stash_cli_app_key("***")
        code, err, result = self._stderr_resolve(api.resolve_app_key)
        self.assertEqual(code, 0)
        self.assertEqual(result[0], RUNTIME_KEY)
        self.assertEqual(result[1], "environment")
        self.assertIn("parameter_ignored=true", err)
        self.assertNotIn(RUNTIME_KEY, err)

    def test_is_auth_error_recognizes_redacted(self):
        self.assertTrue(api._is_auth_error(RuntimeError("AUTH_CONTEXT_REDACTED: x")))

    def test_get_openapi_client_maps_redacted_from_shared_client(self):
        os.environ[RUNTIME_ENV] = RUNTIME_KEY
        mock_mod = MagicMock()
        mock_mod.OpenApiClient.from_runtime.side_effect = RuntimeError(
            "AUTH_CONTEXT_REDACTED: injected"
        )
        with patch.object(api, "_shared_client_spec_exists", return_value=True):
            with patch.dict(sys.modules, {"xg_openapi_client": mock_mod}):
                code, err, _ = self._stderr_resolve(lambda: api.get_openapi_client())
        self.assertEqual(code, 1)
        self.assertIn("AUTH_CONTEXT_REDACTED", err)
        self.assertIn("企业知识库 AppKey", err)
        self.assertNotIn("injected", err)
        self.assertNotIn(RUNTIME_KEY, err)


class TestMaskAndBaseUrl(AuthTestCase):
    def test_mask_short_and_long(self):
        self.assertEqual(api.mask_app_key("abcd"), "****")
        masked = api.mask_app_key("abcdefghijklmnop")
        self.assertIn("********", masked)
        self.assertNotEqual(masked, "abcdefghijklmnop")

    def test_base_url_open_api_once(self):
        self.assertEqual(
            api.normalize_base_url("https://example.com"),
            "https://example.com/open-api",
        )
        self.assertEqual(
            api.normalize_base_url("https://example.com/open-api"),
            "https://example.com/open-api",
        )
        self.assertEqual(
            api.normalize_base_url("https://example.com/open-api/"),
            "https://example.com/open-api",
        )
        path = api.normalize_open_api_path("/open-api/document-database/file/getChildFiles")
        self.assertEqual(path, "/document-database/file/getChildFiles")
        joined = api.normalize_base_url("https://example.com/open-api") + path
        self.assertEqual(joined.count("/open-api"), 1)


class TestClientFactory(AuthTestCase):
    def test_stdlib_when_package_missing(self):
        api.stash_cli_app_key(PARAM_KEY)
        with patch.object(api, "_shared_client_spec_exists", return_value=False):
            buf = io.StringIO()
            with redirect_stderr(buf):
                client = api.get_openapi_client(timeout=60)
        self.assertIsInstance(client, api.StdlibOpenApiClient)
        self.assertIn("OPENAPI_CLIENT_FALLBACK=stdlib", buf.getvalue())
        self.assertFalse(hasattr(client, "upload_file"))

    def test_import_failed_does_not_fallback(self):
        api.stash_cli_app_key(PARAM_KEY)
        with patch.object(api, "_shared_client_spec_exists", return_value=True):
            with patch.dict(sys.modules, {"xg_openapi_client": None}):
                buf = io.StringIO()
                with redirect_stderr(buf):
                    with self.assertRaises(SystemExit):
                        api.get_openapi_client()
                self.assertIn("OPENAPI_CLIENT_IMPORT_FAILED", buf.getvalue())
                self.assertNotIn("OPENAPI_CLIENT_FALLBACK=stdlib", buf.getvalue())


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestStdlibHttp(AuthTestCase):
    def _client(self):
        return api.StdlibOpenApiClient(PARAM_KEY, "https://example.com/open-api", timeout=5)

    def test_get_json_and_appkey_header(self):
        opener = MagicMock()
        opener.open.return_value = FakeResponse(json.dumps({"resultCode": 1, "data": {"ok": True}}).encode())
        with patch.object(api, "build_opener", return_value=opener):
            data = self._client().get("/document-database/app/listAll")
        self.assertEqual(data["resultCode"], 1)
        req = opener.open.call_args[0][0]
        self.assertEqual(req.get_header("Appkey") or req.headers.get("appKey"), PARAM_KEY)

    def test_http_401(self):
        err = HTTPError("https://example.com/x", 401, "Unauthorized", hdrs=None, fp=io.BytesIO(b"secret-body"))
        opener = MagicMock()
        opener.open.side_effect = err
        with patch.object(api, "build_opener", return_value=opener):
            with self.assertRaises(RuntimeError) as cm:
                self._client().get("/x")
        self.assertIn("HTTP 401", str(cm.exception))
        self.assertNotIn(PARAM_KEY, str(cm.exception))
        self.assertNotIn("secret-body", str(cm.exception))

    def test_invalid_json(self):
        opener = MagicMock()
        opener.open.return_value = FakeResponse(b"<html>not json</html>")
        with patch.object(api, "build_opener", return_value=opener):
            with self.assertRaises(RuntimeError) as cm:
                self._client().get("/x")
        self.assertIn("OPENAPI_INVALID_RESPONSE", str(cm.exception))
        self.assertNotIn(PARAM_KEY, str(cm.exception))

    def test_network_error(self):
        opener = MagicMock()
        opener.open.side_effect = URLError("timed out")
        with patch.object(api, "build_opener", return_value=opener):
            with self.assertRaises(RuntimeError) as cm:
                self._client().get("/x")
        self.assertIn("OPENAPI_NETWORK_ERROR", str(cm.exception))
        self.assertNotIn(PARAM_KEY, str(cm.exception))

    def test_timeout_error(self):
        opener = MagicMock()
        opener.open.side_effect = TimeoutError("timeout")
        with patch.object(api, "build_opener", return_value=opener):
            with self.assertRaises(RuntimeError) as cm:
                self._client().get("/x")
        self.assertIn("OPENAPI_NETWORK_ERROR", str(cm.exception))

    def test_cross_origin_redirect_rejected(self):
        handler = api._SameOriginRedirectHandler()
        req = Request("https://a.example/open-api/x", headers={"appKey": PARAM_KEY})
        with self.assertRaises(URLError) as cm:
            handler.redirect_request(req, None, 302, "Found", {}, "https://b.example/x")
        self.assertIn("跨源重定向", str(cm.exception))
        self.assertNotIn(PARAM_KEY, str(cm.exception))

    def test_same_origin_allowed_predicate(self):
        self.assertTrue(api._is_same_origin("https", "a.example", "https://a.example/other"))
        self.assertFalse(api._is_same_origin("https", "a.example", "https://b.example/other"))

    def test_multipart_cross_origin_raises(self):
        api.stash_cli_app_key(PARAM_KEY)
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fh.write(b"hello")
            tmp = fh.name
        self.addCleanup(lambda: os.path.exists(tmp) and os.unlink(tmp))

        class FakeHTTPResponse:
            def __init__(self):
                self.status = 302

            def getheader(self, name):
                return "https://evil.example/steal"

            def read(self):
                return b""

            def close(self):
                return None

        class FakeConn:
            def putrequest(self, *a, **k):
                return None

            def putheader(self, *a, **k):
                return None

            def endheaders(self):
                return None

            def send(self, *a, **k):
                return None

            def getresponse(self):
                return FakeHTTPResponse()

            def close(self):
                return None

        with patch.object(api, "_shared_client_spec_exists", return_value=False):
            with patch("http.client.HTTPSConnection", return_value=FakeConn()):
                with patch.object(api.time, "sleep"):
                    buf = io.StringIO()
                    with redirect_stderr(buf):
                        with self.assertRaises(SystemExit):
                            api.upload_multipart_file("/cwork-file/uploadWholeFile", tmp)
                    self.assertIn("跨源重定向", buf.getvalue())
                    self.assertNotIn(PARAM_KEY, buf.getvalue())


class TestP0SkillFixes(AuthTestCase):
    def test_upsert_share_registers_core_args_and_default_read_preview(self):
        path = SCRIPTS / "share" / "upsert-file-share-grants.py"
        proc = subprocess.run(
            [sys.executable, "-B", str(path), "--help"],
            capture_output=True,
            text=True,
            cwd=str(SKILL_ROOT),
        )
        help_text = (proc.stdout or "") + (proc.stderr or "")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("file_id", help_text)
        self.assertIn("--emp-id", help_text)
        self.assertIn("--permissions", help_text)

        import permissions as perms

        self.assertEqual(perms.DEFAULT_SHARE_PERMISSIONS, ["read", "preview"])
        self.assertEqual(perms.validate_share_permissions(["read", "preview"]), ["read", "preview"])
        with self.assertRaises(ValueError):
            perms.validate_share_permissions(["admin"])
        with self.assertRaises(ValueError):
            perms.ensure_subset_of_ceiling(["read"], None)
        with self.assertRaises(ValueError):
            perms.ensure_subset_of_ceiling(["read"], [])
        # 个人空间 Owner 等：上限常仅含 admin，与服务端跳过子集校验对齐
        perms.ensure_subset_of_ceiling(["read", "preview"], ["admin"])
        with self.assertRaises(ValueError):
            perms.ensure_subset_of_ceiling(["read", "preview"], ["read", "preview"])
        perms.ensure_subset_of_ceiling(["read"], ["read", "preview", "fileshare"])
        with self.assertRaises(ValueError):
            perms.ensure_subset_of_ceiling(["download"], ["read", "preview", "fileshare"])

    def test_permissions_module_is_packaged(self):
        self.assertTrue((COMMON / "permissions.py").is_file())

    def test_add_member_requires_space_expand_ack(self):
        text = (SCRIPTS / "admin" / "add-member.py").read_text(encoding="utf-8")
        self.assertIn("--ack-space-expand", text)
        self.assertIn('ack != "YES"', text)

    def test_list_and_remove_member_scripts(self):
        list_path = SCRIPTS / "admin" / "list-members.py"
        list_org_path = SCRIPTS / "admin" / "list-org-members.py"
        remove_path = SCRIPTS / "admin" / "remove-member.py"
        self.assertTrue(list_path.is_file())
        self.assertTrue(list_org_path.is_file())
        self.assertTrue(remove_path.is_file())
        list_text = list_path.read_text(encoding="utf-8")
        self.assertIn("/admin/listMembers", list_text)
        list_org_text = list_org_path.read_text(encoding="utf-8")
        self.assertIn("/admin/listOrgMembers", list_org_text)
        remove_text = remove_path.read_text(encoding="utf-8")
        self.assertIn("--ack-space-shrink", remove_text)

    def test_org_write_and_role_update_scripts(self):
        add_org = SCRIPTS / "admin" / "add-org-member.py"
        remove_org = SCRIPTS / "admin" / "remove-org-member.py"
        upd_emp = SCRIPTS / "admin" / "update-member-role.py"
        upd_org = SCRIPTS / "admin" / "update-org-member-role.py"
        for path in (add_org, remove_org, upd_emp, upd_org):
            self.assertTrue(path.is_file(), path.name)
        self.assertIn("/admin/addOrgMember", add_org.read_text(encoding="utf-8"))
        self.assertIn("--ack-space-expand", add_org.read_text(encoding="utf-8"))
        self.assertIn("/admin/removeOrgMember", remove_org.read_text(encoding="utf-8"))
        self.assertIn("--ack-role-elevate", upd_emp.read_text(encoding="utf-8"))
        self.assertIn("/admin/updateMemberRole", upd_emp.read_text(encoding="utf-8"))
        self.assertIn("/admin/updateOrgMemberRole", upd_org.read_text(encoding="utf-8"))
        add_emp = SCRIPTS / "admin" / "add-member.py"
        add_text = add_emp.read_text(encoding="utf-8")
        self.assertIn("个人知识库禁止", add_text)
        add_org_text = add_org.read_text(encoding="utf-8")
        self.assertIn("个人知识库禁止", add_org_text)
        upd_text = upd_emp.read_text(encoding="utf-8")
        self.assertIn("个人知识库禁止升权", upd_text)
        upd_org_text = upd_org.read_text(encoding="utf-8")
        self.assertIn("个人知识库禁止升权", upd_org_text)
        self.assertIn('"3.3.7"', (SKILL_ROOT / "version.json").read_text(encoding="utf-8"))

    def test_resolve_path_script_and_navigator_confirm(self):
        resolve_path = SCRIPTS / "browse" / "resolve-path.py"
        self.assertTrue(resolve_path.is_file())
        help_proc = subprocess.run(
            [sys.executable, "-B", str(resolve_path), "--help"],
            capture_output=True,
            text=True,
            cwd=str(SKILL_ROOT),
        )
        help_text = (help_proc.stdout or "") + (help_proc.stderr or "")
        self.assertEqual(help_proc.returncode, 0)
        self.assertIn("--project-id", help_text)
        self.assertIn("--path", help_text)
        self.assertIn("--root-file-id", help_text)
        resolve_text = resolve_path.read_text(encoding="utf-8")
        self.assertIn("/document-database/file/resolvePath", resolve_text)
        self.assertIn("projectName", resolve_text)
        self.assertIn("projectId", resolve_text)
        self.assertIn("exists=false", resolve_text)
        self.assertIn("sys.exit(1)", resolve_text)
        self.assertIn("def normalize_relative_path", resolve_text)
        self.assertIn('replace("\\\\", "/")', resolve_text)

        nav_path = SCRIPTS / "folder-navigator.py"
        nav_text = nav_path.read_text(encoding="utf-8")
        self.assertIn("resolve_path_exact", nav_text)
        self.assertIn("/document-database/file/resolvePath", nav_text)
        self.assertIn("needs_user_confirm", nav_text)
        self.assertIn('match_type in ("multiple", "fuzzy", "best_match")', nav_text)
        self.assertIn("needs_confirm = match_type in", nav_text)
        self.assertIn("def normalize_relative_path", nav_text)
        self.assertIn("lookup_project_name", nav_text)
        self.assertIn('"projectName": project_name', nav_text)
        self.assertIn("--app-code", nav_text)

        version = (SKILL_ROOT / "version.json").read_text(encoding="utf-8")
        self.assertIn('"3.3.7"', version)

        self.assertRegex(
            nav_text,
            r'needs_confirm = match_type in \("multiple", "fuzzy", "best_match"\)',
        )

        # 路径归一规则与两脚本调用点一致
        samples = [
            ("/a/b/", "a/b"),
            ("a\\b\\c", "a/b/c"),
            ("  集团/产品中心/  ", "集团/产品中心"),
        ]
        for raw, expect in samples:
            got = (raw or "").replace("\\", "/").strip().strip("/")
            self.assertEqual(got, expect, raw)
        self.assertIn("normalize_relative_path(args.path)", resolve_text)
        self.assertIn("normalize_relative_path(folder_path)", nav_text)
    def test_upsert_dry_run_skips_ceiling_http(self):
        """无鉴权环境下 --dry-run 仍应成功：证明未调用 getMySharePermissions。"""
        path = SCRIPTS / "share" / "upsert-file-share-grants.py"
        env = {k: v for k, v in os.environ.items() if k != RUNTIME_ENV}
        proc = subprocess.run(
            [sys.executable, "-B", str(path), "1", "--emp-id", "2", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(SKILL_ROOT),
            env=env,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout.strip())
        self.assertTrue(payload.get("dryRun"))
        self.assertEqual(
            payload.get("body", {}).get("shareGrants", [{}])[0].get("permissions"),
            ["read", "preview"],
        )

    def test_batch_get_content_passes_dict_body(self):
        text = (SCRIPTS / "query" / "batch-get-content.py").read_text(encoding="utf-8")
        self.assertIn('body={"files": files}', text)
        self.assertNotIn('.encode("utf-8")', text)

    def test_finalize_version_uses_post(self):
        text = (SCRIPTS / "manage" / "finalize-version.py").read_text(encoding="utf-8")
        self.assertIn('method="POST"', text)
        self.assertIn("body=payload", text)
        self.assertNotIn('method="GET"', text)

    def test_strip_grant_defines_helpers(self):
        text = (SCRIPTS / "grant" / "strip-grant-permissions.py").read_text(encoding="utf-8")
        self.assertIn("def parse_csv", text)
        self.assertIn("def current_permissions", text)

    def test_write_ops_do_not_blind_retry(self):
        text = (COMMON / "docdb_open_api.py").read_text(encoding="utf-8")
        self.assertIn('max_attempts = 3 if method_u == "GET" else 1', text)

    def test_get_download_info_no_public_bypass_flag(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "query" / "get-download-info.py"), "--help"],
            capture_output=True,
            text=True,
            cwd=str(SKILL_ROOT),
        )
        help_text = (proc.stdout or "") + (proc.stderr or "")
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("--bypass-risk", help_text)


if __name__ == "__main__":
    unittest.main()
