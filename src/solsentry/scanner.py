"""Core Solidity scanner.

The scanner deliberately stays small and dependency-free. It combines a
lightweight brace-aware function splitter with rule-specific pattern checks;
it is not a full Solidity compiler or AST parser. Every finding therefore
carries a confidence level and a concrete source location for human review.
"""

from __future__ import annotations

import fnmatch
import os
import re
import time
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path

from .models import Finding, ScanResult
from .rules import RULES_BY_ID

SKIP_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "lib",
    "out",
    "cache",
    "artifacts",
    "dist",
    "build",
    "target",
    "coverage",
}

FUNC_RE = re.compile(
    r"\b(?P<kind>function|constructor|fallback|receive)\b"
    r"(?:\s+(?P<name>[A-Za-z_]\w*))?"
    r"\s*\((?P<params>[^{};]*)\)"
    r"(?P<header>[^{};]*)\{",
    re.MULTILINE,
)

STATE_VAR_RE = re.compile(
    r"^\s*(?P<type>mapping\s*\([^;]*?\)|uint\d*|int\d*|address(?:\s+payable)?|"
    r"bool|string|bytes\d*|[A-Z]\w*(?:\.\w+)?)\s+"
    r"(?:(?:public|private|internal|constant|immutable|override|transient)\s+)*"
    r"(?P<name>[A-Za-z_]\w*)\s*(?:[;=])"
)

EXTERNAL_CALL_RE = re.compile(r"\.\s*(?P<kind>call|send)\s*(?:\{[^}]*\})?\s*\(")
DELEGATECALL_RE = re.compile(r"\.\s*delegatecall\s*\(")
TX_ORIGIN_RE = re.compile(r"\btx\.origin\b")
SELFDESTRUCT_RE = re.compile(r"\b(selfdestruct|suicide)\s*\(")
RANDOM_SOURCE_RE = re.compile(
    r"\b(?:block\.(?:timestamp|number|difficulty|prevrandao|coinbase)|blockhash)\b",
    re.IGNORECASE,
)
RANDOM_CONTEXT_RE = re.compile(
    r"%|keccak256|sha256|rand|seed|winner|lottery|draw|roll", re.IGNORECASE
)
SENSITIVE_NAME_RE = re.compile(
    r"^(?:set[A-Z_]|mint|burn|pause|unpause|upgrade|transferOwnership|"
    r"renounceOwnership|destroy|kill|sweep|rescue|initialize|changeOwner|"
    r"setImplementation|emergency)"
)
AUTH_RE = re.compile(
    r"\b(?:onlyOwner|onlyRole|onlyAdmin|onlyMinter|onlySelf|onlyProxy|"
    r"requiresAuth|_checkOwner|hasRole|isOwner|owner\s*==|msg\.sender\s*==|"
    r"validSignature|confirmed)\b"
)
NON_REENTRANT_RE = re.compile(r"\bnonReentrant\b")
VISIBILITY_RE = re.compile(r"\b(public|external|internal|private)\b")


def strip_comments(source: str) -> str:
    """Replace comments with spaces while preserving newlines and offsets."""

    out: list[str] = []
    i = 0
    length = len(source)
    state = "code"
    quote = ""
    while i < length:
        char = source[i]
        nxt = source[i + 1] if i + 1 < length else ""
        if state == "code":
            if char == "/" and nxt == "/":
                state = "line_comment"
                out.append("  ")
                i += 2
                continue
            if char == "/" and nxt == "*":
                state = "block_comment"
                out.append("  ")
                i += 2
                continue
            if char in ("'", '"'):
                state = "string"
                quote = char
                out.append(char)
                i += 1
                continue
            out.append(char)
            i += 1
            continue
        if state == "line_comment":
            if char == "\n":
                state = "code"
                out.append("\n")
            else:
                out.append(" ")
            i += 1
            continue
        if state == "block_comment":
            if char == "*" and nxt == "/":
                state = "code"
                out.append("  ")
                i += 2
                continue
            out.append("\n" if char == "\n" else " ")
            i += 1
            continue
        # String literal: keep content but make the delimiters inert.
        out.append(char)
        if char == "\\" and i + 1 < length:
            out.append(source[i + 1])
            i += 2
            continue
        if char == quote:
            state = "code"
        i += 1
    return "".join(out)


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for match in re.finditer("\n", text):
        starts.append(match.end())
    return starts


def _line_col(text: str, offset: int, starts: list[int] | None = None) -> tuple[int, int]:
    starts = starts or _line_starts(text)
    index = bisect_right(starts, offset) - 1
    return index + 1, offset - starts[index] + 1


def _match_brace(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


@dataclass(frozen=True)
class FunctionInfo:
    kind: str
    name: str
    header: str
    body: str
    start: int
    body_start: int
    line: int
    end_line: int


def find_functions(code: str) -> list[FunctionInfo]:
    functions: list[FunctionInfo] = []
    occupied_until = -1
    for match in FUNC_RE.finditer(code):
        if match.start() < occupied_until:
            continue
        open_index = match.end() - 1
        close_index = _match_brace(code, open_index)
        if close_index < 0:
            continue
        line, _ = _line_col(code, match.start())
        end_line, _ = _line_col(code, close_index)
        functions.append(
            FunctionInfo(
                kind=match.group("kind"),
                name=match.group("name") or match.group("kind"),
                header=code[match.start() : open_index].strip(),
                body=code[open_index + 1 : close_index],
                start=match.start(),
                body_start=open_index + 1,
                line=line,
                end_line=end_line,
            )
        )
        occupied_until = close_index
    return functions


def collect_state_vars(code: str, functions: list[FunctionInfo]) -> dict[str, int]:
    occupied = [False] * (code.count("\n") + 2)
    for function in functions:
        for line in range(function.line, function.end_line + 1):
            if 0 <= line < len(occupied):
                occupied[line] = True

    variables: dict[str, int] = {}
    for number, line in enumerate(code.splitlines(), start=1):
        if number < len(occupied) and occupied[number]:
            continue
        match = STATE_VAR_RE.match(line)
        if match:
            variables[match.group("name")] = number
    return variables


def _extract_parenthesised(text: str, open_index: int) -> str:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : index]
    return ""


def _superseded_by_check(body: str, call_start: int, call_end: int) -> bool:
    """Best-effort check whether a low-level call result is inspected."""

    before = body[max(0, call_start - 260) : call_start]
    after = body[call_end : call_end + 520]
    variable_names = set(re.findall(r"\bbool\s+([A-Za-z_]\w*)", before))
    variable_names.update(re.findall(r"\(\s*bool\s+([A-Za-z_]\w*)\s*,", before))
    if not variable_names:
        return False
    for name in variable_names:
        if re.search(rf"\brequire\s*\(\s*{re.escape(name)}\b", after):
            return True
        if re.search(rf"\b(?:assert|revert)\s*\(\s*{re.escape(name)}\b", after):
            return True
        if re.search(rf"\bif\s*\(\s*!?\s*{re.escape(name)}\b", after):
            return True
    return False


def _static_delegate_receiver(prefix: str) -> bool:
    """Return True when the delegatecall receiver is a literal/immutable contract."""

    expression = prefix.rstrip()
    if not expression:
        return False
    return bool(
        re.search(
            r"(?:address\s*\(\s*this\s*\)|address\s*\(\s*0x[0-9a-fA-F]{40}\s*\)|"
            r"0x[0-9a-fA-F]{40}|this|[A-Z][A-Z0-9_]*)\s*$",
            expression,
        )
    )


def parse_suppressions(
    original_lines: list[str],
) -> tuple[dict[int, set[str]], set[str]]:
    """Parse ``solsentry-disable*`` comments.

    Returns a line -> rule-id mapping and a file-wide disabled rule set.
    A disable comment without rule ids disables every rule.
    """

    per_line: dict[int, set[str]] = {}
    file_wide: set[str] = set()

    def ids(raw: str) -> set[str]:
        found = set(re.findall(r"SS-\d{3}", raw))
        return found or set(RULES_BY_ID)

    for number, line in enumerate(original_lines, start=1):
        match = re.search(r"solsentry-disable-next-line\b(.*)", line)
        if match:
            per_line.setdefault(number + 1, set()).update(ids(match.group(1)))
            continue
        match = re.search(r"solsentry-disable-line\b(.*)", line)
        if match:
            per_line.setdefault(number, set()).update(ids(match.group(1)))
            continue
        match = re.search(r"solsentry-disable\b(?!-(?:next-line|line))(.*)", line)
        if match:
            file_wide.update(ids(match.group(1)))
    return per_line, file_wide


class Scanner:
    """Scan Solidity sources for a curated set of high-signal risks."""

    def scan(self, paths: list[str], excludes: list[str] | None = None) -> ScanResult:
        started = time.perf_counter()
        excludes = excludes or []
        files = self._discover(paths, excludes)
        target = ", ".join(paths) if paths else "."
        result = ScanResult(target=target)
        if not files:
            result.errors.append("未找到 .sol 文件")
            result.elapsed_ms = int((time.perf_counter() - started) * 1000)
            return result

        seen: set[str] = set()
        for path in files:
            resolved = str(path.resolve()).lower()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                source = path.read_text(encoding="utf-8-sig", errors="replace")
            except OSError as exc:
                result.errors.append(f"{path}: {exc}")
                continue
            display = self._display_path(path)
            findings, suppressed = self.scan_source(
                source, filename=str(path), display=display, apply_suppressions=True
            )
            result.findings.extend(findings)
            result.suppressed += suppressed
            result.files_scanned += 1
            result.lines_scanned += len(source.splitlines()) or 1

        result.findings.sort(
            key=lambda f: (f.file, f.line, f.column, f.rule_id)
        )
        result.elapsed_ms = int((time.perf_counter() - started) * 1000)
        return result

    def scan_text(self, source: str, filename: str = "<memory>") -> list[Finding]:
        findings, _ = self.scan_source(
            source, filename=filename, display=filename, apply_suppressions=True
        )
        return findings

    def scan_source(
        self,
        source: str,
        filename: str,
        display: str | None = None,
        apply_suppressions: bool = True,
    ) -> tuple[list[Finding], int]:
        source = source.replace("\r\n", "\n").replace("\r", "\n")
        display = display or filename
        original_lines = source.splitlines()
        code = strip_comments(source)
        functions = find_functions(code)
        state_vars = collect_state_vars(code, functions)
        suppressions, file_wide = (
            parse_suppressions(original_lines) if apply_suppressions else ({}, set())
        )

        findings: list[Finding] = []
        for function in functions:
            findings.extend(self._reentrancy(function, code, original_lines, state_vars, display))
            findings.extend(self._tx_origin(function, code, original_lines, display))
            findings.extend(self._unchecked_calls(function, code, original_lines, display))
            findings.extend(self._delegatecall(function, code, original_lines, display))
            findings.extend(self._randomness(function, code, original_lines, display))
            findings.extend(self._selfdestruct(function, code, original_lines, display))
            findings.extend(
                self._access_control(function, code, original_lines, state_vars, display)
            )

        unique: dict[tuple[str, int, int], Finding] = {}
        suppressed = 0
        for finding in findings:
            if finding.rule_id in file_wide or finding.rule_id in suppressions.get(
                finding.line, set()
            ):
                suppressed += 1
                continue
            key = (finding.rule_id, finding.line, finding.column)
            unique.setdefault(key, finding)
        return list(unique.values()), suppressed

    # -- discovery -----------------------------------------------------

    @staticmethod
    def _display_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return path.name

    @staticmethod
    def _discover(paths: list[str], excludes: list[str]) -> list[Path]:
        found: list[Path] = []
        for raw in paths or ["."]:
            path = Path(raw)
            if path.is_file() and path.suffix == ".sol":
                found.append(path)
            elif path.is_dir():
                for root, directories, filenames in os.walk(path):
                    directories[:] = [
                        name
                        for name in directories
                        if name not in SKIP_DIRS and not name.startswith(".")
                    ]
                    for filename in filenames:
                        if filename.endswith(".sol"):
                            found.append(Path(root) / filename)
        filtered = []
        for path in sorted(found):
            normalised = path.as_posix()
            if any(
                fnmatch.fnmatch(normalised, pattern)
                or fnmatch.fnmatch(path.name, pattern)
                for pattern in excludes
            ):
                continue
            filtered.append(path)
        return filtered

    # -- rule checks ---------------------------------------------------

    def _finding(
        self,
        rule_id: str,
        display: str,
        code: str,
        original_lines: list[str],
        offset: int,
        function: str,
        message: str,
        confidence: str | None = None,
    ) -> Finding:
        rule = RULES_BY_ID[rule_id]
        line, column = _line_col(code, offset)
        evidence = ""
        if 0 < line <= len(original_lines):
            evidence = original_lines[line - 1].strip()
        if not evidence:
            evidence = code.splitlines()[line - 1].strip() if line <= len(code.splitlines()) else ""
        return Finding(
            rule_id=rule.id,
            title=rule.title,
            severity=rule.severity,
            file=display,
            line=line,
            column=column,
            function=function,
            evidence=evidence[:200],
            message=message,
            remediation=rule.remediation,
            swc=rule.swc,
            cwe=rule.cwe,
            confidence=confidence or rule.confidence,
        )

    def _reentrancy(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        state_vars: dict[str, int],
        display: str,
    ) -> list[Finding]:
        if NON_REENTRANT_RE.search(function.header):
            return []
        for match in EXTERNAL_CALL_RE.finditer(function.body):
            after = function.body[match.end() :]
            for variable in state_vars:
                assignment = re.search(
                    rf"(?<![\w.]){re.escape(variable)}\s*(?:\[[^\]]*\]\s*)?"
                    r"(?:[+\-*/%]?=)",
                    after,
                )
                deletion = re.search(rf"\bdelete\s+{re.escape(variable)}\b", after)
                if assignment or deletion:
                    offset = function.body_start + match.start()
                    return [
                        self._finding(
                            "SS-101",
                            display,
                            code,
                            original_lines,
                            offset,
                            function.name,
                            f"函数 {function.name} 在外部调用后仍更新状态变量 "
                            f"{variable}，存在重入窗口。",
                            "medium",
                        )
                    ]
        return []

    def _tx_origin(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        display: str,
    ) -> list[Finding]:
        match = TX_ORIGIN_RE.search(function.body)
        if not match:
            return []
        return [
            self._finding(
                "SS-102",
                display,
                code,
                original_lines,
                function.body_start + match.start(),
                function.name,
                f"函数 {function.name} 使用 tx.origin 做身份判断；钓鱼合约可诱导"
                "受害者触发调用并继承其权限。",
                "high",
            )
        ]

    def _unchecked_calls(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        display: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for match in EXTERNAL_CALL_RE.finditer(function.body):
            if _superseded_by_check(function.body, match.start(), match.end()):
                continue
            kind = match.group("kind")
            findings.append(
                self._finding(
                    "SS-103",
                    display,
                    code,
                    original_lines,
                    function.body_start + match.start(),
                    function.name,
                    f"函数 {function.name} 的 .{kind} 返回值未被检查，调用失败时"
                    "交易仍会继续执行。",
                    "medium",
                )
            )
        return findings

    def _delegatecall(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        display: str,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for match in DELEGATECALL_RE.finditer(function.body):
            receiver = function.body[: match.start()]
            if _static_delegate_receiver(receiver):
                continue
            findings.append(
                self._finding(
                    "SS-104",
                    display,
                    code,
                    original_lines,
                    function.body_start + match.start(),
                    function.name,
                    f"函数 {function.name} 对动态目标执行 delegatecall，攻击者可能"
                    "控制执行逻辑并改写当前合约存储。",
                    "high",
                )
            )
        return findings

    def _randomness(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        display: str,
    ) -> list[Finding]:
        offset = 0
        for line in function.body.splitlines(keepends=True):
            if RANDOM_SOURCE_RE.search(line) and RANDOM_CONTEXT_RE.search(line):
                return [
                    self._finding(
                        "SS-105",
                        display,
                        code,
                        original_lines,
                        function.body_start + offset,
                        function.name,
                        f"函数 {function.name} 使用区块变量生成随机结果，验证者可预测或"
                        "影响抽取过程。",
                        "medium",
                    )
                ]
            offset += len(line)
        return []

    def _selfdestruct(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        display: str,
    ) -> list[Finding]:
        match = SELFDESTRUCT_RE.search(function.body)
        if not match:
            return []
        return [
            self._finding(
                "SS-106",
                display,
                code,
                original_lines,
                function.body_start + match.start(),
                function.name,
                f"函数 {function.name} 调用 selfdestruct，可能强制转移余额并删除"
                "合约代码，破坏既有安全假设。",
                "high",
            )
        ]

    def _access_control(
        self,
        function: FunctionInfo,
        code: str,
        original_lines: list[str],
        state_vars: dict[str, int],
        display: str,
    ) -> list[Finding]:
        if function.kind != "function" or not SENSITIVE_NAME_RE.match(function.name):
            return []
        visibility = VISIBILITY_RE.search(function.header)
        if not visibility or visibility.group(1) not in ("public", "external"):
            return []
        if AUTH_RE.search(function.header) or AUTH_RE.search(function.body):
            return []

        writes_state = any(
            re.search(
                rf"(?<![\w.]){re.escape(variable)}\s*(?:\[[^\]]*\]\s*)?(?:[+\-*/%]?=)",
                function.body,
            )
            for variable in state_vars
        )
        risky_effect = bool(
            SELFDESTRUCT_RE.search(function.body)
            or DELEGATECALL_RE.search(function.body)
            or EXTERNAL_CALL_RE.search(function.body)
        )
        if not (writes_state or risky_effect):
            return []

        return [
            self._finding(
                "SS-107",
                display,
                code,
                original_lines,
                function.start,
                function.name,
                f"敏感函数 {function.name} 为 public/external 且未见权限校验，"
                "任意地址均可调用并修改关键状态。",
                "low",
            )
        ]
