from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("write_gate.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("write_gate_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WriteGateTest(unittest.TestCase):
    def _ws(self) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        return Path(tmpdir.name)

    def _write_log(self, ws: Path, rows: list[dict]) -> Path:
        path = ws / "http_log.jsonl"
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )
        return path

    def _write_consent(self, ws: Path, content: str) -> Path:
        path = ws / "write_consent_log.md"
        path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
        return path

    def test_passes_when_workspace_has_no_log_files(self):
        module = _load_module()
        ws = self._ws()

        result = module.check_write_gate(ws)

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["summary"]["write_calls"], 0)

    def test_passes_when_http_log_has_only_reads(self):
        module = _load_module()
        ws = self._ws()
        self._write_log(
            ws,
            [
                {
                    "ts": "2026-05-12T22:30:00+08:00",
                    "analysis_id": "WEB-001",
                    "method": "GET",
                    "url": "https://example.com/api/list",
                    "status": 200,
                    "allow_write": False,
                    "consent_match": None,
                    "rejected_reason": None,
                }
            ],
        )

        result = module.check_write_gate(ws)

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["summary"]["write_calls"], 0)
        self.assertEqual(result["summary"]["read_calls"], 1)

    def test_fails_when_write_call_has_no_consent_match(self):
        module = _load_module()
        ws = self._ws()
        self._write_log(
            ws,
            [
                {
                    "ts": "2026-05-12T22:30:00+08:00",
                    "analysis_id": "WEB-001",
                    "method": "POST",
                    "url": "https://example.com/api/create",
                    "status": 201,
                    "allow_write": True,
                    "consent_match": None,
                    "rejected_reason": None,
                }
            ],
        )

        result = module.check_write_gate(ws)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("WEB-001", joined)
        self.assertIn("consent_match", joined)

    def test_passes_when_write_call_has_consent_match(self):
        module = _load_module()
        ws = self._ws()
        self._write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "ok create"
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )
        self._write_log(
            ws,
            [
                {
                    "ts": "2026-05-12T22:35:00+08:00",
                    "analysis_id": "WEB-001",
                    "method": "POST",
                    "url": "https://example.com/api/create",
                    "status": 201,
                    "allow_write": True,
                    "consent_match": "abc123",
                    "rejected_reason": None,
                }
            ],
        )

        result = module.check_write_gate(ws)

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["summary"]["write_calls"], 1)

    def test_fails_when_consent_entry_has_empty_user_reply(self):
        module = _load_module()
        ws = self._ws()
        self._write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim:
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )

        result = module.check_write_gate(ws)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("user_reply_verbatim", joined)

    def test_fails_when_consent_entry_has_invalid_approved_at(self):
        module = _load_module()
        ws = self._ws()
        self._write_consent(
            ws,
            """
            - analysis_ids: [WEB-001]
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "ok"
              approved_at: not-a-timestamp
            """,
        )

        result = module.check_write_gate(ws)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("approved_at", joined)

    def test_fails_when_consent_entry_has_empty_analysis_ids(self):
        module = _load_module()
        ws = self._ws()
        self._write_consent(
            ws,
            """
            - analysis_ids: []
              method: POST
              url_pattern: https://example.com/api/create*
              user_reply_verbatim: "ok"
              approved_at: 2026-05-12T22:30:00+08:00
            """,
        )

        result = module.check_write_gate(ws)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("analysis_ids", joined)

    def test_summary_counts_rejected_writes_separately(self):
        module = _load_module()
        ws = self._ws()
        self._write_log(
            ws,
            [
                {
                    "ts": "2026-05-12T22:30:00+08:00",
                    "analysis_id": "WEB-001",
                    "method": "POST",
                    "url": "https://example.com/api/create",
                    "status": None,
                    "allow_write": False,
                    "consent_match": None,
                    "rejected_reason": "missing_allow_write",
                }
            ],
        )

        result = module.check_write_gate(ws)

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["summary"]["write_calls"], 0)
        self.assertEqual(result["summary"]["rejected_writes"], 1)

    def test_cli_exit_code_matches_result(self):
        module = _load_module()
        ws = self._ws()

        rc = module.run([str(ws)])
        self.assertEqual(rc, 0)

        self._write_log(
            ws,
            [
                {
                    "ts": "2026-05-12T22:30:00+08:00",
                    "analysis_id": "WEB-001",
                    "method": "POST",
                    "url": "https://example.com/api/create",
                    "status": 201,
                    "allow_write": True,
                    "consent_match": None,
                    "rejected_reason": None,
                }
            ],
        )

        rc2 = module.run([str(ws)])
        self.assertEqual(rc2, 1)


if __name__ == "__main__":
    unittest.main()
