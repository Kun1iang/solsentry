"""Data models shared by the scanner, reporters, and CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from . import __version__
from .rules import (
    RULES_BY_ID,
    SEVERITY_LABELS,
    SEVERITY_ORDER,
    SEVERITY_WEIGHTS,
)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass(frozen=True)
class Finding:
    """A single issue reported by the scanner."""

    rule_id: str
    title: str
    severity: str
    file: str
    line: int
    column: int
    function: str
    evidence: str
    message: str
    remediation: str
    swc: str
    cwe: str
    confidence: str

    @property
    def severity_label(self) -> str:
        return SEVERITY_LABELS.get(self.severity, self.severity)

    @property
    def location(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity,
            "severity_label": self.severity_label,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "function": self.function,
            "evidence": self.evidence,
            "message": self.message,
            "remediation": self.remediation,
            "swc": self.swc,
            "cwe": self.cwe,
            "confidence": self.confidence,
        }


@dataclass
class ScanResult:
    """Aggregated result of scanning one or more Solidity files."""

    target: str
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    lines_scanned: int = 0
    suppressed: int = 0
    elapsed_ms: int = 0
    generated_at: str = field(default_factory=_now)
    errors: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts = {severity: 0 for severity in SEVERITY_ORDER}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        counts["total"] = len(self.findings)
        return counts

    @property
    def risk_score(self) -> int:
        score = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in self.findings)
        return min(100, score)

    @property
    def grade(self) -> str:
        score = self.risk_score
        if score <= 9:
            return "A"
        if score <= 24:
            return "B"
        if score <= 49:
            return "C"
        if score <= 74:
            return "D"
        return "F"

    @property
    def risk_label(self) -> str:
        return {
            "A": "低风险",
            "B": "低风险",
            "C": "中风险",
            "D": "高风险",
            "F": "严重风险",
        }[self.grade]

    def sorted_findings(self) -> list[Finding]:
        return sorted(
            self.findings,
            key=lambda f: (
                SEVERITY_ORDER.get(f.severity, 9),
                f.file,
                f.line,
                f.rule_id,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        counts = self.counts()
        return {
            "tool": {"name": "SolSentry", "version": __version__},
            "target": self.target,
            "generated_at": self.generated_at,
            "summary": {
                **counts,
                "risk_score": self.risk_score,
                "grade": self.grade,
                "risk_label": self.risk_label,
                "files_scanned": self.files_scanned,
                "lines_scanned": self.lines_scanned,
                "suppressed": self.suppressed,
                "elapsed_ms": self.elapsed_ms,
                "rules": list(RULES_BY_ID),
            },
            "findings": [finding.to_dict() for finding in self.sorted_findings()],
            "errors": list(self.errors),
        }
