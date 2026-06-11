from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("tdrs_gate.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("tdrs_gate_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TdrsGateTest(unittest.TestCase):
    def _write_analysis(self, content: str) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "test_analysis.md"
        path.write_text(content.strip() + "\n", encoding="utf-8")
        return path

    def test_closed_row_requires_live_query_evidence_and_backfilled_url(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | load more | CLOSED | owner=foo 的列表样本 |  | owners=foo | 命中 group=123 | https://example.com/list |  |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        self.assertIn("WEB-001", "\n".join(result["errors"]))
        self.assertIn("CLOSED", "\n".join(result["errors"]))
        self.assertIn("查数API", "\n".join(result["errors"]))

    def test_unverified_row_requires_attempt_evidence_not_empty_classification(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | owner scope | UNVERIFIED | strategy-only owner 样本 |  |  |  |  |  |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        self.assertIn("UNVERIFIED", "\n".join(result["errors"]))
        self.assertIn("attempt evidence", "\n".join(result["errors"]))

    def test_terminal_rows_with_evidence_pass_without_all_closed(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | load more | CLOSED | owner=foo 的列表样本 | GET /api/strategy/list | owners=foo | 命中 group=123 | https://example.com/list?owners=foo | live API 200，样本当前存在 |
| WEB-002 | missing owner | BLOCKED | strategy-only owner 样本 | GET /api/strategy/list | owners=bar | 403，无 owner scope |  | 缺 owner scope，进入 Gate C |
| WEB-003 | external data | manual-prep | 需要外部导入原料 |  |  |  |  | 已向用户请求人工鉴权/导入支持，用户明确无法提供，进入 Gate C |
| WEB-004 | flaky backend | UNVERIFIED | 大数据量样本 | GET /api/strategy/list | limit=1000 | API 500 |  | 已按预算尝试，接口失败 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["summary"]["total"], 4)
        self.assertEqual(result["summary"]["CLOSED"], 1)
        self.assertEqual(result["summary"]["BLOCKED"], 1)
        self.assertEqual(result["summary"]["manual-prep"], 1)
        self.assertEqual(result["summary"]["UNVERIFIED"], 1)

    def test_attempt_budget_prevents_query_loops(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 | 查询次数 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- | -------- |
| WEB-001 | repeated query | UNVERIFIED | owner=foo 的列表样本 | GET /api/strategy/list | owners=foo | 空结果 |  | 已反复查询仍无样本 | 3 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        self.assertIn("query attempt budget", "\n".join(result["errors"]))

    def test_no_live_sample_data_provided_is_not_decision_evidence(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | owner scope | manual-prep | strategy-only owner 样本 |  |  |  |  | no live sample data provided |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        self.assertIn("no live sample data", "\n".join(result["errors"]))
        self.assertIn("ask user", "\n".join(result["errors"]))

    def test_missing_auth_can_terminal_only_after_user_request_evidence(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | owner scope | BLOCKED | strategy-only owner 样本 |  |  |  |  | 已向用户请求鉴权 curl 和 owner scope，用户明确无法提供，进入 Gate C |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertTrue(result["passed"], result["errors"])

    def test_compact_tdrs_evidence_column_keeps_analysis_table_readable(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | 前置条件 | 操作步骤 | 预期结果 | TDRS状态 | TDRS证据 |
| ------ | -------- | -------- | -------- | -------- | -------- | -------- |
| WEB-001 | load more | URL 已回填 | 点击 Load more | 展示更多结果 | CLOSED | 数据要求=owner=foo 的列表样本; 查数API=GET /api/strategy/list; 查数参数=owners=foo; 查数结果=命中 group=123; 回填URL=https://example.com/list?owners=foo; 裁决证据=live API 200，样本当前存在; 查询次数=1; 造数次数=0 |
| WEB-002 | owner scope | 缺 owner scope | 人工补齐 owner | 可进入页面 | BLOCKED | 数据要求=strategy-only owner 样本; 查数API=GET /api/strategy/list; 查数参数=owners=bar; 查数结果=403，无 owner scope; 裁决证据=403 证明当前账号无 owner scope，需切换账号; 查询次数=1; 造数次数=0 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["summary"]["total"], 2)
        self.assertEqual(result["summary"]["CLOSED"], 1)
        self.assertEqual(result["summary"]["BLOCKED"], 1)

    def test_compact_unverified_missing_auth_requires_user_request_not_plain_result(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | 前置条件 | 操作步骤 | 预期结果 | TDRS状态 | TDRS证据 |
| ------ | -------- | -------- | -------- | -------- | -------- | -------- |
| WEB-001 | owner scope | 缺 owner scope | 人工补齐 owner | 可进入页面 | UNVERIFIED | 数据要求=strategy-only owner 样本; 查数结果=缺少鉴权/API 信息，无法查数; 裁决证据=缺少鉴权/API 信息; 查询次数=0; 造数次数=0 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("查数API", joined)
        self.assertIn("auth scaffold", joined)

    def test_unverified_row_with_curl_in_evidence_but_no_query_api_is_rejected(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | metrics rendering | UNVERIFIED | getMetricsV2 返回的样本指标 |  |  |  |  | 用户提供的 curl 只覆盖 ticket 查询，没有覆盖 getMetricsV2，HTTP 200 only for ticket |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("WEB-001", joined)
        self.assertIn("查数API", joined)
        self.assertIn("auth scaffold", joined)

    def test_unverified_row_with_query_api_but_no_result_signal_is_rejected(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | metrics rendering | UNVERIFIED | getMetricsV2 返回的样本指标 | POST /api/getMetricsV2 | ticketId=5341 | 待查 |  | 还没跑 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        joined = "\n".join(result["errors"])
        self.assertIn("WEB-001", joined)
        self.assertIn("查数结果", joined)

    def test_unverified_row_with_query_api_and_real_signal_passes(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | TDRS状态 | 数据要求 | 查数API | 查数参数 | 查数结果 | 回填URL | 裁决证据 |
| ------ | -------- | -------- | -------- | ------- | -------- | -------- | ------ | -------- |
| WEB-001 | metrics rendering | UNVERIFIED | getMetricsV2 返回的样本指标 | POST /api/getMetricsV2 | ticketId=5341 | 200，indicators 为空 |  | 接口可达但无样本，已按预算 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertTrue(result["passed"], result["errors"])

    def test_requested_material_without_user_outcome_is_not_terminal_evidence(self):
        module = _load_module()
        analysis = self._write_analysis(
            """
# 测试分析文档

| 分析ID | 测试场景 | 前置条件 | 操作步骤 | 预期结果 | TDRS状态 | TDRS证据 |
| ------ | -------- | -------- | -------- | -------- | -------- | -------- |
| WEB-001 | release observation | demo 页存在但缺 strategy API | 人工补齐鉴权 | 可进入页面 | UNVERIFIED | 数据要求=ReleaseObservation Strategy GetAffectedEntities 样本; 查数结果=缺失鉴权/API 信息; 裁决证据=代码证据: GetAffectedEntities TODO，占位；缺失鉴权且已请求材料; 查询次数=0; 造数次数=0 |
            """
        )

        result = module.check_tdrs_gate(analysis)

        self.assertFalse(result["passed"])
        self.assertIn("explicit user outcome", "\n".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
