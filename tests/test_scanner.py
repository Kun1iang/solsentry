from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solsentry.scanner import Scanner  # noqa: E402


class ExampleScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scanner = Scanner()

    def test_clean_examples_have_no_findings(self) -> None:
        result = self.scanner.scan([str(ROOT / "examples" / "clean")])
        self.assertEqual(result.files_scanned, 2)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.risk_score, 0)
        self.assertEqual(result.grade, "A")

    def test_vulnerable_examples_cover_all_rules(self) -> None:
        result = self.scanner.scan([str(ROOT / "examples" / "vulnerable")])
        self.assertEqual(result.files_scanned, 3)
        found = {(finding.rule_id, Path(finding.file).name) for finding in result.findings}
        expected = {
            ("SS-101", "Bank.sol"),
            ("SS-102", "Bank.sol"),
            ("SS-102", "Lottery.sol"),
            ("SS-103", "Bank.sol"),
            ("SS-104", "Proxy.sol"),
            ("SS-105", "Lottery.sol"),
            ("SS-106", "Proxy.sol"),
            ("SS-107", "Bank.sol"),
            ("SS-107", "Proxy.sol"),
        }
        self.assertTrue(expected.issubset(found), expected - found)
        self.assertEqual(len(result.findings), 11)
        self.assertGreater(result.risk_score, 0)

    def test_findings_are_sorted_by_severity(self) -> None:
        result = self.scanner.scan([str(ROOT / "examples" / "vulnerable")])
        severities = [finding.severity for finding in result.sorted_findings()]
        self.assertEqual(severities[:4], ["high", "high", "high", "high"])


class RuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scanner = Scanner()

    def test_reentrancy_after_external_call(self) -> None:
        source = """
        contract C {
            mapping(address => uint256) public balances;
            function withdraw() external {
                (bool ok, ) = msg.sender.call{value: balances[msg.sender]}("");
                require(ok);
                balances[msg.sender] = 0;
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-101", ids)

    def test_checks_effects_interactions_is_clean(self) -> None:
        source = """
        contract C {
            mapping(address => uint256) public balances;
            function withdraw() external {
                uint256 amount = balances[msg.sender];
                balances[msg.sender] = 0;
                (bool ok, ) = msg.sender.call{value: amount}("");
                require(ok);
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertNotIn("SS-101", ids)

    def test_tx_origin(self) -> None:
        source = """
        contract C {
            address owner;
            function f() external { require(tx.origin == owner); }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-102", ids)

    def test_unchecked_call(self) -> None:
        source = """
        contract C {
            function f(address payable to) external {
                to.call{value: 1}("");
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-103", ids)

    def test_checked_call_is_clean(self) -> None:
        source = """
        contract C {
            function f(address payable to) external {
                (bool ok, ) = to.call{value: 1}("");
                require(ok, "failed");
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertNotIn("SS-103", ids)

    def test_dynamic_delegatecall(self) -> None:
        source = """
        contract C {
            function f(address target, bytes calldata data) external {
                (bool ok, ) = target.delegatecall(data);
                require(ok);
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-104", ids)

    def test_static_delegatecall_is_clean(self) -> None:
        source = """
        contract C {
            function f(bytes calldata data) external {
                (bool ok, ) = address(this).delegatecall(data);
                require(ok);
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertNotIn("SS-104", ids)

    def test_weak_randomness(self) -> None:
        source = """
        contract C {
            function draw() external {
                uint256 n = uint256(keccak256(abi.encodePacked(block.timestamp))) % 10;
                require(n >= 0);
            }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-105", ids)

    def test_selfdestruct(self) -> None:
        source = """
        contract C {
            function kill() external { selfdestruct(payable(msg.sender)); }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-106", ids)

    def test_missing_access_control(self) -> None:
        source = """
        contract C {
            address public owner;
            function setOwner(address next) external { owner = next; }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertIn("SS-107", ids)

    def test_only_owner_is_clean(self) -> None:
        source = """
        contract C {
            address public owner;
            modifier onlyOwner() { require(msg.sender == owner); _; }
            function setOwner(address next) external onlyOwner { owner = next; }
        }
        """
        ids = {finding.rule_id for finding in self.scanner.scan_text(source)}
        self.assertNotIn("SS-107", ids)


class SuppressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scanner = Scanner()

    def test_next_line_suppression(self) -> None:
        source = """
        contract C {
            address owner;
            function f() external {
                // solsentry-disable-next-line SS-102
                require(tx.origin == owner);
            }
        }
        """
        findings, suppressed = self.scanner.scan_source(source, "C.sol")
        self.assertEqual([finding for finding in findings if finding.rule_id == "SS-102"], [])
        self.assertEqual(suppressed, 1)

    def test_line_suppression(self) -> None:
        source = """
        contract C {
            address owner;
            function f() external {
                require(tx.origin == owner); // solsentry-disable-line SS-102
            }
        }
        """
        findings, suppressed = self.scanner.scan_source(source, "C.sol")
        self.assertEqual([finding for finding in findings if finding.rule_id == "SS-102"], [])
        self.assertEqual(suppressed, 1)

    def test_file_suppression(self) -> None:
        source = """
        // solsentry-disable SS-102
        contract C {
            address owner;
            function f() external { require(tx.origin == owner); }
        }
        """
        findings, suppressed = self.scanner.scan_source(source, "C.sol")
        self.assertEqual([finding for finding in findings if finding.rule_id == "SS-102"], [])
        self.assertEqual(suppressed, 1)


if __name__ == "__main__":
    unittest.main()
