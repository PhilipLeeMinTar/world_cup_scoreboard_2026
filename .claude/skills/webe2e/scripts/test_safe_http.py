from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("safe_http.py")


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_consent(workspace: Path, content: str) -> Path:
    path = workspace / "write_consent_log.md"
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    return path


def _fake_transport(*, status: int = 200, body: str = "{}"):
    calls: list[dict] = []

    def transport(method: str, url: str, headers: dict, body_bytes: bytes | None):
        calls.append({"method": method, "url": url, "headers": dict(headers), "body": body_bytes})
        return {"status": status, "body": body}

    transport.calls = calls  # type: ignore[attr-defined]
    return transport


def _frozen_now(iso: str):
    target = dt.datetime.fromisoformat(iso)

    def now():
        return target

    return now


class SafeHttpTest(unittest.TestCase):
    def _tmp(self) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        return Path(tmpdir.name)

    def _module(self, name: str):
        return _load_module(name)

    def test_get_passes_without_allow_write_and_writes_audit(self):
        module = self._module("safe_http_t1")
        ws = self._tmp()
        transport = _fake_transport(status=200, body="ok")

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "GET",
                "--url", "https://example.com/api/list",
            ],
            transport=transport,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(len(transport.calls), 1)
        log_path = ws / "http_log.jsonl"
        self.assertTrue(log_path.exists())
        entry = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["method"], "GET")
        self.assertEqual(entry["analysis_id"], "WEB-001")
        self.assertEqual(entry["status"], 200)
        self.assertIsNone(entry["consent_match"])

    def test_head_passes_without_allow_write(self):
        module = self._module("safe_http_t1b")
        ws = self._tmp()
        transport = _fake_transport(status=200, body="")

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "HEAD",
                "--url", "https://example.com/api/list",
            ],
            transport=transport,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(transport.calls[0]["method"], "HEAD")

    def test_post_without_allow_write_is_rejected_and_audits_rejection(self):
        module = self._module("safe_http_t2")
        ws = self._tmp()
        transport = _fake_transport()
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            rc = module.run(
                [
                    "--workspace", str(ws),
                    "--analysis-id", "WEB-001",
                    "--method", "POST",
                    "--url", "https://example.com/api/create",
                ],
                transport=transport,
            )

        self.assertEqual(rc, 2)
        self.assertEqual(len(transport.calls), 0)
        self.assertIn("--allow-write", stderr.getvalue())
        log_path = ws / "http_log.jsonl"
        self.assertTrue(log_path.exists())
        entry = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["method"], "POST")
        self.assertEqual(entry["status"], None)
        self.assertEqual(entry["rejected_reason"], "missing_allow_write")

    def test_post_with_allow_write_but_no_consent_log_exits_3(self):
        module = self._module("safe_http_t3")
        ws = self._tmp()
        transport = _fake_transport()
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            rc = module.run(
                [
                    "--workspace", str(ws),
                    "--analysis-id", "WEB-001",
                    "--method", "POST",
                    "--url", "https://example.com/api/create",
                    "--allow-write",
                ],
                transport=transport,
            )

        self.assertEqual(rc, 3)
        self.assertEqual(len(transport.calls), 0)
        self.assertIn("write_consent_log", stderr.getvalue())

    def test_post_with_matching_consent_passes_and_logs_match_id(self):
        module = self._module("safe_http_t4")
        ws = self._tmp()
        _write_consent(
            ws,
            """
            # Write Consent Log

            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "可以创建，只给我的账号"
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )
        transport = _fake_transport(status=201, body='{"id":1}')

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "POST",
                "--url", "https://example.com/api/create?owner=foo",
                "--allow-write",
            ],
            transport=transport,
            now=_frozen_now("2026-05-12T22:45:00+08:00"),
        )

        self.assertEqual(rc, 0)
        self.assertEqual(len(transport.calls), 1)
        entry = json.loads((ws / "http_log.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["method"], "POST")
        self.assertEqual(entry["status"], 201)
        self.assertIsNotNone(entry["consent_match"])

    def test_post_with_consent_but_analysis_id_mismatch_is_rejected(self):
        module = self._module("safe_http_t5")
        ws = self._tmp()
        _write_consent(
            ws,
            """
            - analysis_ids: [WEB-002]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "ok"
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )
        transport = _fake_transport()

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "POST",
                "--url", "https://example.com/api/create",
                "--allow-write",
            ],
            transport=transport,
            now=_frozen_now("2026-05-12T22:45:00+08:00"),
        )

        self.assertEqual(rc, 3)
        self.assertEqual(len(transport.calls), 0)

    def test_post_with_consent_but_method_mismatch_is_rejected(self):
        module = self._module("safe_http_t6")
        ws = self._tmp()
        _write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "ok"
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )
        transport = _fake_transport()

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "DELETE",
                "--url", "https://example.com/api/create/1",
                "--allow-write",
            ],
            transport=transport,
            now=_frozen_now("2026-05-12T22:45:00+08:00"),
        )

        self.assertEqual(rc, 3)
        self.assertEqual(len(transport.calls), 0)

    def test_post_with_consent_but_url_pattern_no_match_is_rejected(self):
        module = self._module("safe_http_t7")
        ws = self._tmp()
        _write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/strategy/*
              user_reply_verbatim: "ok"
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )
        transport = _fake_transport()

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "POST",
                "--url", "https://example.com/api/user/create",
                "--allow-write",
            ],
            transport=transport,
            now=_frozen_now("2026-05-12T22:45:00+08:00"),
        )

        self.assertEqual(rc, 3)
        self.assertEqual(len(transport.calls), 0)

    def test_post_with_expired_consent_is_rejected(self):
        module = self._module("safe_http_t8")
        ws = self._tmp()
        _write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "ok"
              approved_at: 2026-05-12T20:00:00+08:00
            """,
        )
        transport = _fake_transport()

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "POST",
                "--url", "https://example.com/api/create",
                "--allow-write",
                "--max-consent-age-minutes", "30",
            ],
            transport=transport,
            now=_frozen_now("2026-05-12T22:45:00+08:00"),
        )

        self.assertEqual(rc, 3)
        self.assertEqual(len(transport.calls), 0)

    def test_post_with_consent_but_empty_user_reply_is_rejected(self):
        module = self._module("safe_http_t9")
        ws = self._tmp()
        _write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim:
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )
        transport = _fake_transport()

        rc = module.run(
            [
                "--workspace", str(ws),
                "--analysis-id", "WEB-001",
                "--method", "POST",
                "--url", "https://example.com/api/create",
                "--allow-write",
            ],
            transport=transport,
            now=_frozen_now("2026-05-12T22:45:00+08:00"),
        )

        self.assertEqual(rc, 3)
        self.assertEqual(len(transport.calls), 0)

    def test_unknown_method_is_rejected_with_exit_2(self):
        module = self._module("safe_http_t10")
        ws = self._tmp()
        with self.assertRaises(SystemExit) as ctx:
            module.run(
                [
                    "--workspace", str(ws),
                    "--analysis-id", "WEB-001",
                    "--method", "TRACE",
                    "--url", "https://example.com",
                ],
                transport=_fake_transport(),
            )
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
