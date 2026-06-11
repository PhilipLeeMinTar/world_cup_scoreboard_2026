from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("case_management.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("case_management_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SaveResponseExpectationExtractionTest(unittest.TestCase):
    def test_format_save_response_persists_bits_expectation_nodes_with_case_paths(self):
        module = _load_module()
        case_md = "\n".join(
            [
                "# Demo",
                "",
                "#### 用例数量-exp2.2",
                "##### **操作步骤** step1",
                "##### **预期结果** exp1",
                "##### **预期结果** exp2",
                "##### **操作步骤** step2.1",
                "##### **预期结果** exp2.2",
                "##### **操作步骤** step2.2",
                "##### **预期结果** exp2.2",
            ]
        )
        response = {
            "data": {
                "case_url": {"caseId": 11352425},
                "case_data": {
                    "children": [
                        {
                            "title": "用例数量-exp2.2",
                            "children": [
                                {"node_type": "预期结果", "id": "xb7janfd5ujqzb", "title": "exp1"},
                                {"node_type": "预期结果", "id": "cti3lttc3vmkjj", "title": "exp2"},
                                {"node_type": "预期结果", "id": "dqytvqbvwh2zm6", "title": "exp2.2"},
                                {"node_type": "预期结果", "id": "zp5esbk2fxsva7", "title": "exp2.2"},
                            ],
                        }
                    ]
                },
            }
        }

        formatted = module._format_save_response(
            response,
            devops_id=310499123202,
            case_content=case_md,
        )

        self.assertEqual(
            formatted["data"]["case_detail_url"],
            "https://bits.bytedance.net/devops/310499123202/quality/case/caseDetail/11352425",
        )
        self.assertEqual(
            formatted["data"]["case_expectations"],
            [
                {
                    "case_index": 0,
                    "case_title": "用例数量-exp2.2",
                    "expectation_nodes": [
                        {
                            "path": [0, 0],
                            "id": "xb7janfd5ujqzb",
                            "expected_result": "exp1",
                            "bits_text": "exp1",
                        },
                        {
                            "path": [0, 1],
                            "id": "cti3lttc3vmkjj",
                            "expected_result": "exp2",
                            "bits_text": "exp2",
                        },
                        {
                            "path": [1, 0],
                            "id": "dqytvqbvwh2zm6",
                            "expected_result": "exp2.2",
                            "bits_text": "exp2.2",
                        },
                        {
                            "path": [2, 0],
                            "id": "zp5esbk2fxsva7",
                            "expected_result": "exp2.2",
                            "bits_text": "exp2.2",
                        },
                    ],
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
