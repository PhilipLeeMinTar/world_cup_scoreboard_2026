from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("case_grammar_check.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("case_grammar_check_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AnalysisCaseMappingGateTest(unittest.TestCase):
    def _write(self, path: Path, content: str) -> None:
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")

    def test_analysis_file_requires_one_case_per_analysis_id(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analysis = tmp / "test_analysis.md"
            case_md = tmp / "case.md"
            self._write(
                analysis,
                """
                # 测试分析文档

                | 分析ID | 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
                | ------ | -------- | -------- | -------- | -------- |
                | A-001 | load more [P0] | URL 已回填 | 点击 Load more | 展示更多结果 |
                | A-002 | URL 持久化 [P0] | URL 已回填 | 刷新页面 | 筛选参数保留 |
                """,
            )
            self._write(
                case_md,
                """
                # case

                #### **测试点** Load more
                **[analysis-id]** A-001
                ##### **前置条件** 访问: https://example.com/list
                **[tag]** e2e
                ##### **操作步骤** 点击 Load more
                ##### **预期结果** 展示更多结果
                """,
            )
            nodes, parse_rule = module.parse_markdown(case_md.read_text(encoding="utf-8"))
            self.assertTrue(parse_rule.passed)
            module.link_tree(nodes)

            rule = module.check_analysis_case_mapping(
                nodes,
                module.parse_analysis_ids(analysis),
            )

        self.assertFalse(rule.passed)
        self.assertIn("A-002", "\n".join(rule.errors))
        self.assertIn("case count", "\n".join(rule.errors))

    def test_case_cannot_merge_multiple_analysis_ids(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analysis = tmp / "test_analysis.md"
            case_md = tmp / "case.md"
            self._write(
                analysis,
                """
                # 测试分析文档

                | 分析ID | 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
                | ------ | -------- | -------- | -------- | -------- |
                | A-001 | load more [P0] | URL 已回填 | 点击 Load more | 展示更多结果 |
                | A-002 | URL 持久化 [P0] | URL 已回填 | 刷新页面 | 筛选参数保留 |
                """,
            )
            self._write(
                case_md,
                """
                # case

                #### **测试点** Load more and URL
                **[analysis-id]** A-001,A-002
                ##### **前置条件** 访问: https://example.com/list
                **[tag]** e2e
                ##### **操作步骤** 点击 Load more 后刷新
                ##### **预期结果** 展示更多结果
                ##### **预期结果** 筛选参数保留
                """,
            )
            nodes, parse_rule = module.parse_markdown(case_md.read_text(encoding="utf-8"))
            self.assertTrue(parse_rule.passed)
            module.link_tree(nodes)

            rule = module.check_analysis_case_mapping(
                nodes,
                module.parse_analysis_ids(analysis),
            )

        self.assertFalse(rule.passed)
        self.assertIn("multiple analysis ids", "\n".join(rule.errors))

    def test_complete_one_to_one_mapping_passes(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analysis = tmp / "test_analysis.md"
            case_md = tmp / "case.md"
            self._write(
                analysis,
                """
                # 测试分析文档

                | 分析ID | 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
                | ------ | -------- | -------- | -------- | -------- |
                | A-001 | load more [P0] | URL 已回填 | 点击 Load more | 展示更多结果 |
                | A-002 | URL 持久化 [P0] | URL 已回填 | 刷新页面 | 筛选参数保留 |
                """,
            )
            self._write(
                case_md,
                """
                # case

                #### **测试点** Load more
                **[analysis-id]** A-001
                ##### **前置条件** 访问: https://example.com/list
                **[tag]** e2e
                ##### **操作步骤** 点击 Load more
                ##### **预期结果** 展示更多结果

                #### **测试点** URL 持久化
                **[analysis-id]** A-002
                ##### **前置条件** 访问: https://example.com/list
                **[tag]** e2e
                ##### **操作步骤** 刷新页面
                ##### **预期结果** 筛选参数保留
                """,
            )
            nodes, parse_rule = module.parse_markdown(case_md.read_text(encoding="utf-8"))
            self.assertTrue(parse_rule.passed)
            module.link_tree(nodes)

            rule = module.check_analysis_case_mapping(
                nodes,
                module.parse_analysis_ids(analysis),
            )

        self.assertTrue(rule.passed, rule.errors)


if __name__ == "__main__":
    unittest.main()
