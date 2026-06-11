"""Tests for screenshot collection and narrative rendering in case2webe2e.

These tests pin three bugs reported against ``analyze-task``:

1. The narrative referenced retry-execution screenshots (e.g. execution-2)
   but the download loop only collected the first execution's screenshots,
   producing broken image links in the rendered report.
2. ``_trim_text(..., limit=120)`` silently truncated multi-path screenshot
   summaries, leaving dangling ``...`` paths in ``key_evidence``.
3. Screenshots were emitted as plain text paths, so IDE markdown preview
   could not inline-render the frames.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("case2webe2e.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("case2webe2e_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _payload(executions):
    return {"executions": executions}


class CollectScreenshotRelpathsTest(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_aggregates_first_step_screenshots_across_executions(self):
        payload = _payload(
            [
                {
                    "tasks": [
                        {"screenshots": ["execution-1-task-1-a.jpeg"], "status": "passed"},
                        {"screenshots": ["execution-1-task-2-x.jpeg"], "status": "failed"},
                    ]
                },
                {
                    "tasks": [
                        {"screenshots": ["execution-2-task-1-b.jpeg"], "status": "passed"},
                        {"screenshots": ["execution-2-task-2-y.jpeg"], "status": "failed"},
                    ]
                },
            ]
        )

        first, _failure = self.module._collect_report_screenshot_relpaths(payload)

        self.assertIn("execution-1-task-1-a.jpeg", first)
        self.assertIn("execution-2-task-1-b.jpeg", first)

    def test_aggregates_failure_screenshots_across_executions(self):
        payload = _payload(
            [
                {
                    "tasks": [
                        {"screenshots": ["execution-1-task-1-a.jpeg"], "status": "passed"},
                        {"screenshots": ["execution-1-task-2-x.jpeg"], "status": "failed"},
                    ]
                },
                {
                    "tasks": [
                        {"screenshots": ["execution-2-task-1-b.jpeg"], "status": "passed"},
                        {"screenshots": ["execution-2-task-2-y.jpeg"], "status": "failed"},
                    ]
                },
            ]
        )

        _first, failure = self.module._collect_report_screenshot_relpaths(payload)

        self.assertIn("execution-1-task-2-x.jpeg", failure)
        self.assertIn("execution-2-task-2-y.jpeg", failure)

    def test_dedupes_across_executions(self):
        payload = _payload(
            [
                {"tasks": [{"screenshots": ["dup.jpeg"], "status": "passed"}]},
                {"tasks": [{"screenshots": ["dup.jpeg"], "status": "passed"}]},
            ]
        )

        first, _failure = self.module._collect_report_screenshot_relpaths(payload)

        self.assertEqual(first.count("dup.jpeg"), 1)

    def test_handles_missing_payload_safely(self):
        self.assertEqual(self.module._collect_report_screenshot_relpaths(None), ([], []))
        self.assertEqual(self.module._collect_report_screenshot_relpaths({}), ([], []))
        self.assertEqual(
            self.module._collect_report_screenshot_relpaths({"executions": "not-a-list"}),
            ([], []),
        )

    def test_skips_non_dict_tasks(self):
        payload = _payload(
            [
                {"tasks": [None, {"screenshots": ["a.jpeg"], "status": "failed"}]},
            ]
        )

        first, failure = self.module._collect_report_screenshot_relpaths(payload)

        self.assertEqual(first, ["a.jpeg"])
        self.assertEqual(failure, ["a.jpeg"])


class FormatScreenshotEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_renders_markdown_image_syntax(self):
        line = self.module._format_screenshot_evidence(
            "首步截图",
            paths=["analysis_screenshots/123/execution-1-task-1-a.jpeg"],
            relpaths=["execution-1-task-1-a.jpeg"],
        )

        self.assertTrue(line.startswith("首步截图："))
        self.assertIn(
            "![首步截图](analysis_screenshots/123/execution-1-task-1-a.jpeg)",
            line,
        )

    def test_renders_multiple_paths_inline(self):
        line = self.module._format_screenshot_evidence(
            "首步截图",
            paths=[
                "analysis_screenshots/123/execution-1-task-1-a.jpeg",
                "analysis_screenshots/123/execution-2-task-1-b.jpeg",
            ],
            relpaths=None,
        )

        self.assertIn(
            "![首步截图](analysis_screenshots/123/execution-1-task-1-a.jpeg)",
            line,
        )
        self.assertIn(
            "![首步截图](analysis_screenshots/123/execution-2-task-1-b.jpeg)",
            line,
        )

    def test_does_not_truncate_long_paths(self):
        long_path = (
            "analysis_screenshots/5114649265628792084/"
            "execution-1-task-1-e8fb76d6-aaaa-bbbb-cccc-deadbeefcafe.jpeg"
        )
        line = self.module._format_screenshot_evidence(
            "首步截图",
            paths=[long_path, long_path.replace("execution-1", "execution-2")],
            relpaths=None,
        )

        self.assertNotIn("...", line)
        self.assertIn(long_path, line)

    def test_falls_back_to_relpath_when_no_local_path(self):
        line = self.module._format_screenshot_evidence(
            "首步截图",
            paths=None,
            relpaths=["execution-1-task-1-a.jpeg"],
        )

        self.assertTrue(line)
        self.assertIn("未本地落盘", line)
        self.assertIn("`execution-1-task-1-a.jpeg`", line)

    def test_returns_empty_when_no_paths_or_relpaths(self):
        self.assertEqual(
            self.module._format_screenshot_evidence("首步截图", paths=None, relpaths=None),
            "",
        )
        self.assertEqual(
            self.module._format_screenshot_evidence("首步截图", paths=[], relpaths=[]),
            "",
        )


class ClassifyCaseKeyEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()

    def test_uses_markdown_image_syntax_for_screenshots(self):
        result = self.module._classify_case(
            first_step_name="step1",
            failed_step_name="step2 click submit",
            error_message="timeout",
            reasoning_content="",
            loop_signal=None,
            first_screenshot_summary="Markdown 报告首步截图: execution-2-task-1-a.jpeg",
            failed_screenshot_summary="Markdown 报告失败步骤截图: execution-2-task-2-x.jpeg",
            first_screenshot_paths=["analysis_screenshots/777/execution-2-task-1-a.jpeg"],
            failure_screenshot_paths=["analysis_screenshots/777/execution-2-task-2-x.jpeg"],
        )

        joined = "\n".join(result["key_evidence"])

        self.assertIn(
            "![首步截图](analysis_screenshots/777/execution-2-task-1-a.jpeg)",
            joined,
        )
        self.assertIn(
            "![失败截图](analysis_screenshots/777/execution-2-task-2-x.jpeg)",
            joined,
        )

    def test_does_not_truncate_long_screenshot_lines(self):
        long_first = (
            "analysis_screenshots/5114649265628792084/"
            "execution-1-task-1-e8fb76d6-aaaa-bbbb-cccc-deadbeefcafe.jpeg"
        )
        long_failure = (
            "analysis_screenshots/5114649265628792084/"
            "execution-2-task-2-9f9f9f9f-1111-2222-3333-444455556666.jpeg"
        )

        result = self.module._classify_case(
            first_step_name="step1",
            failed_step_name="step2",
            error_message="timeout",
            reasoning_content="",
            loop_signal=None,
            first_screenshot_summary="Markdown 报告首步截图: long-path.jpeg",
            failed_screenshot_summary="Markdown 报告失败步骤截图: long-failure.jpeg",
            first_screenshot_paths=[long_first],
            failure_screenshot_paths=[long_failure],
        )

        joined = "\n".join(result["key_evidence"])

        self.assertIn(long_first, joined, f"long first path got truncated: {joined!r}")
        self.assertIn(long_failure, joined, f"long failure path got truncated: {joined!r}")

    def test_falls_back_to_relpath_when_local_paths_missing(self):
        result = self.module._classify_case(
            first_step_name="step1",
            failed_step_name="step2",
            error_message="timeout",
            reasoning_content="",
            loop_signal=None,
            first_screenshot_summary="Markdown 报告首步截图: rel-first.jpeg",
            failed_screenshot_summary="Markdown 报告失败步骤截图: rel-failure.jpeg",
            first_screenshot_paths=[],
            failure_screenshot_paths=[],
            first_screenshot_relpaths=["rel-first.jpeg"],
            failure_screenshot_relpaths=["rel-failure.jpeg"],
        )

        joined = "\n".join(result["key_evidence"])

        self.assertIn("`rel-first.jpeg`", joined)
        self.assertIn("`rel-failure.jpeg`", joined)
        self.assertIn("未本地落盘", joined)


if __name__ == "__main__":
    unittest.main()
