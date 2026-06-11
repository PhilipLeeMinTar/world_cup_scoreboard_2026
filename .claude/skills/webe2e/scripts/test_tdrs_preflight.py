from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("tdrs_preflight.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("tdrs_preflight_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TdrsPreflightTest(unittest.TestCase):
    def _workspace(self) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        return Path(tmpdir.name)

    def _write(self, workspace: Path, name: str, content: str) -> Path:
        path = workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
        return path

    def test_fails_when_no_auth_assets_present(self):
        module = _load_module()
        workspace = self._workspace()

        result = module.check_preflight(workspace)

        self.assertFalse(result["passed"])
        self.assertEqual(result["present_assets"], [])
        message = "\n".join(result["errors"])
        self.assertIn("AskQuestion", message)
        self.assertIn("auth_log.md", message)

    def test_passes_when_env_file_has_token_like_content(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(
            workspace,
            ".env",
            """
            TSOP_COOKIE=abc123def456
            TSOP_X_CSRF_TOKEN=zzz
            """,
        )

        result = module.check_preflight(workspace)

        self.assertTrue(result["passed"], result["errors"])
        self.assertIn("env", result["present_assets"])

    def test_empty_env_file_does_not_pass(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(workspace, ".env", "\n# only comments\n")

        result = module.check_preflight(workspace)

        self.assertFalse(result["passed"])
        self.assertNotIn("env", result["present_assets"])

    def test_passes_when_save_result_json_exists_with_payload(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(
            workspace,
            "save_result.json",
            """
            {"code": 0, "data": {"devops_id": 1, "case_expectations": [{"id": "abc"}]}}
            """,
        )

        result = module.check_preflight(workspace)

        self.assertTrue(result["passed"], result["errors"])
        self.assertIn("save_result", result["present_assets"])

    def test_empty_save_result_json_does_not_pass(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(workspace, "save_result.json", "{}\n")

        result = module.check_preflight(workspace)

        self.assertFalse(result["passed"])
        self.assertNotIn("save_result", result["present_assets"])

    def test_passes_when_auth_log_records_user_reply(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(
            workspace,
            "auth_log.md",
            """
            # Auth Log

            - analysis_ids: [WEB-001]
              asked_at: 2026-05-12T21:00:00+08:00
              prompt: "需要 TSOP recall-strategy list curl 或 cookie"
              user_reply_verbatim: "我没有这个 owner scope，跳过吧"
              outcome: declined
            """,
        )

        result = module.check_preflight(workspace)

        self.assertTrue(result["passed"], result["errors"])
        self.assertIn("auth_log", result["present_assets"])

    def test_auth_log_without_user_reply_does_not_pass(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(
            workspace,
            "auth_log.md",
            """
            # Auth Log

            - analysis_ids: [WEB-001]
              asked_at: 2026-05-12T21:00:00+08:00
              prompt: "需要 TSOP recall-strategy list curl"
              user_reply_verbatim:
              outcome: pending
            """,
        )

        result = module.check_preflight(workspace)

        self.assertFalse(result["passed"])
        self.assertNotIn("auth_log", result["present_assets"])

    def test_auth_log_with_only_question_no_reply_does_not_pass(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(
            workspace,
            "auth_log.md",
            """
            # Auth Log

            我向用户请求了鉴权 curl，材料还没拿到。
            """,
        )

        result = module.check_preflight(workspace)

        self.assertFalse(result["passed"])
        self.assertNotIn("auth_log", result["present_assets"])

    def test_passes_when_cookies_txt_exists_with_content(self):
        module = _load_module()
        workspace = self._workspace()
        self._write(
            workspace,
            "cookies.txt",
            """
            # Netscape HTTP Cookie File
            .example.com\tTRUE\t/\tTRUE\t9999999999\tsessionid\tabc123
            """,
        )

        result = module.check_preflight(workspace)

        self.assertTrue(result["passed"], result["errors"])
        self.assertIn("cookies", result["present_assets"])

    def test_failure_message_lists_concrete_next_actions(self):
        module = _load_module()
        workspace = self._workspace()

        result = module.check_preflight(workspace)

        joined = "\n".join(result["errors"])
        self.assertIn("AskQuestion", joined)
        self.assertIn(".env", joined)
        self.assertIn("cookies.txt", joined)
        self.assertIn("save_result.json", joined)
        self.assertIn("auth_log.md", joined)
        self.assertIn("user_reply_verbatim", joined)

    def test_cli_exit_code_matches_result(self):
        module = _load_module()
        workspace = self._workspace()

        rc = module.run([str(workspace)])

        self.assertEqual(rc, 1)

        self._write(workspace, ".env", "X_TOKEN=abc\n")
        rc2 = module.run([str(workspace)])
        self.assertEqual(rc2, 0)


if __name__ == "__main__":
    unittest.main()
