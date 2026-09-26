from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solsentry.models import ScanResult
from solsentry.report import render_html, render_json, render_markdown, render_sarif  # noqa: E402
from solsentry.scanner import Scanner  # noqa: E402


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = Scanner().scan([str(ROOT / "examples" / "vulnerable")])

    def test_json_round_trip(self) -> None:
        payload = json.loads(render_json(self.result))
        self.assertEqual(payload["summary"]["total"], len(self.result.findings))
        self.assertEqual(payload["summary"]["grade"], self.result.grade)

    def test_markdown_contains_summary_and_findings(self) -> None:
        text = render_markdown(self.result)
        self.assertIn("# SolSentry 扫描报告", text)
        self.assertIn("SS-101", text)
        self.assertIn("修复建议", text)

    def test_sarif_has_rules_and_results(self) -> None:
        payload = json.loads(render_sarif(self.result))
        run = payload["runs"][0]
        self.assertEqual(len(run["tool"]["driver"]["rules"]), 7)
        self.assertEqual(len(run["results"]), len(self.result.findings))
        self.assertEqual(run["results"][0]["ruleId"], "SS-101")

    def test_html_escapes_evidence(self) -> None:
        result = ScanResult(
            target="inline",
            findings=[],
        )
        # The renderer must not crash on an empty result.
        html = render_html(result)
        self.assertIn("未发现匹配规则的风险", html)

    def test_html_contains_severity_filter(self) -> None:
        html = render_html(self.result)
        self.assertIn('data-filter="high"', html)
        self.assertIn("风险明细", html)


if __name__ == "__main__":
    unittest.main()
