"""Command-line interface for SolSentry_28."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .models import ScanResult
from .report import render_console, render_html, render_json, render_markdown, render_sarif
from .rules import RULES, SEVERITY_LABELS, SEVERITY_ORDER
from .scanner import Scanner

FAIL_LEVELS = {"critical", "high", "medium", "low", "info", "none"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solsentry",
        description="SolSentry_28 — 面向 Solidity 的轻量级静态风险扫描器",
    )
    parser.add_argument("-V", "--version", action="version", version=f"SolSentry_28 {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    scan = subparsers.add_parser("scan", help="扫描 Solidity 合约")
    scan.add_argument("paths", nargs="*", default=["."], help="文件或目录（默认当前目录）")
    scan.add_argument(
        "-f",
        "--format",
        choices=["console", "json", "markdown", "html", "sarif"],
        default="console",
        help="输出格式（默认 console）",
    )
    scan.add_argument("-o", "--output", help="写入文件；HTML 未指定时默认 solsentry_28-report.html")
    scan.add_argument(
        "--min-severity",
        choices=list(SEVERITY_ORDER),
        default="info",
        help="仅展示不低于该等级的问题（默认 info）",
    )
    scan.add_argument(
        "--fail-on",
        choices=sorted(FAIL_LEVELS),
        default="high",
        help="出现不低于该等级的问题时以退出码 1 结束（默认 high）",
    )
    scan.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="排除匹配的文件或目录，可重复",
    )
    scan.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="控制台颜色（默认 auto）",
    )
    scan.add_argument("--quiet", action="store_true", help="只输出报告，不输出额外提示")

    rules = subparsers.add_parser("rules", help="列出内置规则")
    rules.add_argument("--json", action="store_true", help="以 JSON 输出")
    return parser


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", None)
        if encoding and encoding.lower().replace("-", "") not in ("utf8", "utf8sig"):
            try:
                stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
            except (AttributeError, ValueError):
                pass


def _filtered(result: ScanResult, minimum: str) -> list:
    threshold = SEVERITY_ORDER[minimum]
    return [finding for finding in result.findings if SEVERITY_ORDER[finding.severity] <= threshold]


def _should_fail(result: ScanResult, fail_on: str) -> bool:
    if fail_on == "none":
        return False
    threshold = SEVERITY_ORDER[fail_on]
    return any(SEVERITY_ORDER[finding.severity] <= threshold for finding in result.findings)


def _render(result: ScanResult, fmt: str, color: bool) -> str:
    if fmt == "console":
        return render_console(result, color=color)
    if fmt == "json":
        return render_json(result)
    if fmt == "markdown":
        return render_markdown(result)
    if fmt == "sarif":
        return render_sarif(result)
    if fmt == "html":
        return render_html(result)
    raise ValueError(f"unknown format: {fmt}")


def _write(text: str, output: str | None) -> None:
    if not output:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    if not text.endswith("\n"):
        text += "\n"
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _print_rules(as_json: bool) -> int:
    if as_json:
        import json

        payload = [
            {
                "id": rule.id,
                "title": rule.title,
                "severity": rule.severity,
                "swc": rule.swc,
                "cwe": rule.cwe,
                "confidence": rule.confidence,
                "description": rule.description,
                "remediation": rule.remediation,
            }
            for rule in RULES
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    header = f"{'ID':<7} {'等级':<7} {'SWC':<9} {'CWE':<9} 规则"
    print(header)
    print("-" * 78)
    for rule in RULES:
        print(
            f"{rule.id:<7} {SEVERITY_LABELS[rule.severity]:<7} "
            f"{rule.swc:<9} {rule.cwe:<9} {rule.title}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rules":
        return _print_rules(args.json)
    if args.command != "scan":
        parser.print_help()
        return 2

    scanner = Scanner()
    result = scanner.scan(args.paths, excludes=args.exclude)
    if args.min_severity != "info":
        result.findings = _filtered(result, args.min_severity)

    color = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())
    output = args.output
    if args.format == "html" and not output:
        output = "solsentry_28-report.html"
    text = _render(result, args.format, color)
    _write(text, output)

    if output and not args.quiet:
        print(f"报告已写入: {output}", file=sys.stderr)
    if result.errors and not args.quiet:
        for error in result.errors:
            print(f"错误: {error}", file=sys.stderr)

    if result.errors and result.files_scanned == 0:
        return 2
    return 1 if _should_fail(result, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
