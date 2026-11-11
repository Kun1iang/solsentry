from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "solsentry", *args],
        cwd=str(cwd or ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class CliTests(unittest.TestCase):
    def test_clean_examples_exit_zero(self) -> None:
        completed = run_cli("scan", "examples/clean", "--fail-on", "high")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("未发现匹配规则的风险", completed.stdout)

    def test_vulnerable_examples_exit_one(self) -> None:
        completed = run_cli("scan", "examples/vulnerable", "--fail-on", "high")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("SS-101", completed.stdout)
        self.assertIn("风险分", completed.stdout)

    def test_fail_on_none_disables_failure(self) -> None:
        completed = run_cli("scan", "examples/vulnerable", "--fail-on", "none")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_json_output_is_machine_readable(self) -> None:
        completed = run_cli("scan", "examples/vulnerable", "--format", "json")
        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["tool"]["name"], "SolSentry_28")
        self.assertEqual(payload["summary"]["total"], 11)
        self.assertEqual(payload["summary"]["files_scanned"], 3)

    def test_sarif_output_is_valid_json(self) -> None:
        completed = run_cli("scan", "examples/vulnerable", "--format", "sarif")
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["version"], "2.1.0")
        self.assertEqual(payload["runs"][0]["tool"]["driver"]["name"], "SolSentry_28")
        self.assertGreater(len(payload["runs"][0]["results"]), 0)

    def test_html_report_written_to_file(self) -> None:
        output_dir = ROOT / "build" / "test-output"
        shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "report.html"
        completed = run_cli(
            "scan",
            "examples/vulnerable",
            "--format",
            "html",
            "--output",
            str(output),
        )
        self.assertEqual(completed.returncode, 1)
        text = output.read_text(encoding="utf-8")
        self.assertIn("SolSentry_28", text)
        self.assertIn("SS-101", text)

    def test_rules_command(self) -> None:
        completed = run_cli("rules")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("SS-101", completed.stdout)
        self.assertIn("Reentrancy", completed.stdout)

    def test_rules_json(self) -> None:
        completed = run_cli("rules", "--json")
        payload = json.loads(completed.stdout)
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload[0]["id"], "SS-101")


if __name__ == "__main__":
    unittest.main()
