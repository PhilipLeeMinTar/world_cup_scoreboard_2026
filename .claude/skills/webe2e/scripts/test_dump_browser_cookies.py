from __future__ import annotations

import http.cookiejar
import importlib.util
import io
import os
import stat
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).with_name("dump_browser_cookies.py")
PREFLIGHT_PATH = Path(__file__).with_name("tdrs_preflight.py")


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cookie(name: str, value: str, domain: str) -> http.cookiejar.Cookie:
    return http.cookiejar.Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=domain.startswith("."),
        path="/",
        path_specified=True,
        secure=False,
        expires=int(time.time()) + 3600,
        discard=False,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )


def _make_fake_bc3(cookies_by_browser: dict[str, list[http.cookiejar.Cookie]]):
    def _make_reader(cookies: list[http.cookiejar.Cookie]):
        def reader(domain_name: str = ""):
            jar = http.cookiejar.CookieJar()
            for cookie in cookies:
                jar.set_cookie(cookie)
            return jar

        return reader

    return SimpleNamespace(**{name: _make_reader(jar) for name, jar in cookies_by_browser.items()})


class DumpBrowserCookiesTest(unittest.TestCase):
    def _tmp(self) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        return Path(tmpdir.name)

    def test_missing_browser_cookie3_prints_install_hint_and_exits_2(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_1")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            rc = module.run(["--domain", "example.com"], module=None, _force_missing=True)
        text = stderr.getvalue()
        self.assertEqual(rc, 2)
        self.assertIn("pipx install browser_cookie3", text)
        self.assertIn("python3 -m pip install --user browser_cookie3", text)

    def test_writes_netscape_file_with_cookies_for_domain(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_2")
        workspace = self._tmp()
        out_path = workspace / "cookies.txt"
        bc3 = _make_fake_bc3(
            {"chrome": [_make_cookie("sessionid", "abc123", ".example.com")]}
        )

        rc = module.run(
            ["--domain", "example.com", "--out", str(out_path)],
            module=bc3,
        )

        self.assertEqual(rc, 0)
        self.assertTrue(out_path.exists())
        content = out_path.read_text(encoding="utf-8")
        self.assertIn("# Netscape HTTP Cookie File", content)
        self.assertIn("example.com", content)
        self.assertIn("sessionid", content)

    def test_print_only_lists_cookies_without_writing_file(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_3")
        workspace = self._tmp()
        out_path = workspace / "cookies.txt"
        bc3 = _make_fake_bc3(
            {"chrome": [_make_cookie("sessionid", "abc123", ".example.com")]}
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            rc = module.run(
                ["--domain", "example.com", "--out", str(out_path), "--print-only"],
                module=bc3,
            )

        self.assertEqual(rc, 0)
        self.assertFalse(out_path.exists())
        self.assertIn("sessionid", stdout.getvalue())
        self.assertIn("example.com", stdout.getvalue())

    def test_output_file_permission_is_0600(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_4")
        workspace = self._tmp()
        out_path = workspace / "cookies.txt"
        bc3 = _make_fake_bc3(
            {"chrome": [_make_cookie("sessionid", "abc123", ".example.com")]}
        )

        rc = module.run(
            ["--domain", "example.com", "--out", str(out_path)],
            module=bc3,
        )

        self.assertEqual(rc, 0)
        mode = stat.S_IMODE(os.stat(out_path).st_mode)
        self.assertEqual(mode, 0o600)

    def test_empty_domain_argument_is_rejected(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_5")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            rc = module.run(["--domain", "   "], module=_make_fake_bc3({"chrome": []}))
        self.assertEqual(rc, 2)
        self.assertIn("--domain", stderr.getvalue())

    def test_unknown_browser_is_rejected_with_exit_2(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_6")
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as ctx:
            module.run(["--domain", "example.com", "--browser", "lynx"], module=_make_fake_bc3({"chrome": []}))
        self.assertEqual(ctx.exception.code, 2)

    def test_no_cookies_for_domain_returns_dedicated_exit_code(self):
        module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_7")
        workspace = self._tmp()
        out_path = workspace / "cookies.txt"
        bc3 = _make_fake_bc3({"chrome": []})

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            rc = module.run(
                ["--domain", "example.com", "--out", str(out_path)],
                module=bc3,
            )

        self.assertEqual(rc, 4)
        self.assertFalse(out_path.exists())
        self.assertIn("no cookies", stderr.getvalue().lower())

    def test_output_satisfies_tdrs_preflight(self):
        dump_module = _load_module(SCRIPT_PATH, "dump_browser_cookies_under_test_8")
        self.assertTrue(
            PREFLIGHT_PATH.exists(),
            f"expected preflight script at {PREFLIGHT_PATH}",
        )
        preflight_module = _load_module(PREFLIGHT_PATH, "tdrs_preflight_for_dump_test")
        workspace = self._tmp()
        out_path = workspace / "cookies.txt"
        bc3 = _make_fake_bc3(
            {"chrome": [_make_cookie("sessionid", "abc123", ".example.com")]}
        )

        rc = dump_module.run(
            ["--domain", "example.com", "--out", str(out_path)],
            module=bc3,
        )
        self.assertEqual(rc, 0)

        result = preflight_module.check_preflight(workspace)
        self.assertTrue(result["passed"], result["errors"])
        self.assertIn("cookies", result["present_assets"])


if __name__ == "__main__":
    unittest.main()
