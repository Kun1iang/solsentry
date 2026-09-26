"""Output renderers: console, JSON, Markdown, SARIF, and standalone HTML."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Iterable

from . import __version__
from .models import Finding, ScanResult
from .rules import RULES, RULES_BY_ID, SEVERITY_LABELS, SEVERITY_ORDER

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "gray": "\033[90m",
}


def _paint(text: str, *styles: str, color: bool = True) -> str:
    if not color:
        return text
    prefix = "".join(ANSI.get(style, "") for style in styles)
    return f"{prefix}{text}{ANSI['reset']}"


def _severity_colour(severity: str) -> str:
    return {
        "critical": "magenta",
        "high": "red",
        "medium": "yellow",
        "low": "cyan",
        "info": "blue",
    }.get(severity, "gray")


def render_console(result: ScanResult, color: bool = True) -> str:
    lines: list[str] = []
    title = _paint("SolSentry", "bold", "cyan", color=color)
    version = _paint(f"v{__version__}", "gray", color=color)
    lines.append(f"{title} {version}  ·  Solidity 静态风险扫描器")
    lines.append(f"目标: {result.target}")
    lines.append(
        f"扫描: {result.files_scanned} 个文件 / {result.lines_scanned} 行"
        f"  ·  用时 {result.elapsed_ms} ms"
    )
    lines.append("")

    findings = result.sorted_findings()
    if not findings:
        lines.append(_paint("未发现匹配规则的风险。", "green", "bold", color=color))
    for finding in findings:
        label = SEVERITY_LABELS.get(finding.severity, finding.severity)
        badge = _paint(
            f"[{finding.severity.upper()}]",
            "bold",
            _severity_colour(finding.severity),
            color=color,
        )
        lines.append(
            f"{badge} {_paint(finding.rule_id, 'bold', color=color)}  "
            f"{finding.title}  "
            f"{_paint(finding.location, 'gray', color=color)}"
        )
        lines.append(f"  函数: {finding.function}  ·  等级: {label}  ·  {finding.swc} / {finding.cwe}")
        lines.append(f"  证据: {finding.evidence}")
        lines.append(f"  说明: {finding.message}")
        lines.append(f"  修复: {finding.remediation}")
        lines.append("")

    counts = result.counts()
    parts = [
        f"{counts.get(severity, 0)} {SEVERITY_LABELS[severity]}"
        for severity in SEVERITY_ORDER
        if counts.get(severity, 0)
    ]
    summary = " / ".join(parts) if parts else "0 个问题"
    score = _paint(
        f"{result.risk_score}/100 ({result.grade})",
        "bold",
        "green" if result.risk_score < 25 else "yellow" if result.risk_score < 50 else "red",
        color=color,
    )
    lines.append(
        f"结果: {counts['total']} 个问题（{summary}）  ·  风险分 {score}"
        f"  ·  抑制 {result.suppressed} 条"
    )
    if result.errors:
        lines.append(_paint("错误:", "red", "bold", color=color))
        lines.extend(f"  - {error}" for error in result.errors)
    return "\n".join(lines)


def render_json(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


def _md_escape(text: str) -> str:
    return text.replace("`", "\\`").replace("|", "\\|")


def render_markdown(result: ScanResult) -> str:
    counts = result.counts()
    lines = [
        "# SolSentry 扫描报告",
        "",
        f"> 目标：`{result.target}`  ",
        f"> 生成时间：{result.generated_at}  ",
        f"> 工具版本：SolSentry v{__version__}",
        "",
        "## 概览",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| 文件 / 行数 | {result.files_scanned} / {result.lines_scanned} |",
        f"| 问题总数 | {counts['total']} |",
        f"| 风险分 | {result.risk_score}/100（{result.grade}，{result.risk_label}） |",
        f"| 抑制 / 错误 | {result.suppressed} / {len(result.errors)} |",
        "",
        "## 风险分布",
        "",
        "| 等级 | 数量 |",
        "| --- | ---: |",
    ]
    for severity in SEVERITY_ORDER:
        lines.append(f"| {SEVERITY_LABELS[severity]} | {counts.get(severity, 0)} |")
    lines.extend(["", "## 发现", ""])

    findings = result.sorted_findings()
    if not findings:
        lines.append("未发现匹配规则的风险。")
    for number, finding in enumerate(findings, start=1):
        lines.extend(
            [
                f"### {number}. [{SEVERITY_LABELS[finding.severity]}] "
                f"{finding.rule_id} {finding.title}",
                "",
                f"- 位置：`{finding.location}`",
                f"- 函数：`{finding.function}`",
                f"- 置信度：{finding.confidence}",
                f"- 参考：{finding.swc} / {finding.cwe}",
                f"- 证据：`{_md_escape(finding.evidence)}`",
                "",
                finding.message,
                "",
                f"**修复建议：** {finding.remediation}",
                "",
            ]
        )
    if result.errors:
        lines.extend(["## 错误", ""])
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines).rstrip() + "\n"


def _sarif_level(severity: str) -> str:
    if severity in ("critical", "high"):
        return "error"
    if severity == "medium":
        return "warning"
    return "note"


def render_sarif(result: ScanResult) -> str:
    rule_index = {rule.id: index for index, rule in enumerate(RULES)}
    rules = []
    for rule in RULES:
        rules.append(
            {
                "id": rule.id,
                "name": rule.title.replace(" ", ""),
                "shortDescription": {"text": rule.title},
                "fullDescription": {"text": rule.description},
                "helpUri": f"https://swcregistry.io/docs/{rule.swc}",
                "properties": {
                    "tags": ["security", "solidity", rule.swc, rule.cwe],
                    "precision": rule.confidence,
                },
            }
        )

    results = []
    for finding in result.sorted_findings():
        results.append(
            {
                "ruleId": finding.rule_id,
                "ruleIndex": rule_index[finding.rule_id],
                "level": _sarif_level(finding.severity),
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.file},
                            "region": {
                                "startLine": finding.line,
                                "startColumn": finding.column,
                            },
                        }
                    }
                ],
                "partialFingerprints": {
                    "solsentry/v1": f"{finding.rule_id}:{finding.file}:{finding.line}"
                },
                "properties": {
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "swc": finding.swc,
                    "cwe": finding.cwe,
                },
            }
        )

    document = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SolSentry",
                        "version": __version__,
                        "informationUri": "https://github.com/Yaokunliang/solsentry",
                        "rules": rules,
                    }
                },
                "invocations": [
                    {
                        "executionSuccessful": not result.errors,
                        "endTimeUtc": datetime.now().astimezone().isoformat(timespec="seconds"),
                    }
                ],
                "artifacts": [
                    {"location": {"uri": path}}
                    for path in sorted({finding.file for finding in result.findings})
                ],
                "results": results,
            }
        ],
    }
    return json.dumps(document, ensure_ascii=False, indent=2)


# -- HTML -----------------------------------------------------------------

SEVERITY_COLOURS = {
    "critical": "#b42318",
    "high": "#d92d20",
    "medium": "#b54708",
    "low": "#026aa2",
    "info": "#475467",
}

SEVERITY_BG = {
    "critical": "#fef3f2",
    "high": "#fef3f2",
    "medium": "#fffaeb",
    "low": "#f0f9ff",
    "info": "#f8f9fc",
}


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _finding_html(finding: Finding) -> str:
    colour = SEVERITY_COLOURS.get(finding.severity, "#475467")
    background = SEVERITY_BG.get(finding.severity, "#f8f9fc")
    label = SEVERITY_LABELS.get(finding.severity, finding.severity)
    return f"""
    <article class="finding" data-severity="{_e(finding.severity)}" style="--severity:{colour};--severity-bg:{background}">
      <div class="finding-head">
        <span class="badge">{_e(finding.severity.upper())}</span>
        <span class="rule-id">{_e(finding.rule_id)}</span>
        <h2>{_e(finding.title)}</h2>
        <span class="location">{_e(finding.location)}</span>
      </div>
      <div class="meta-line">
        <span>函数 <code>{_e(finding.function)}</code></span>
        <span>置信度 {_e(finding.confidence)}</span>
        <span>{_e(finding.swc)}</span>
        <span>{_e(finding.cwe)}</span>
        <span>{_e(label)}</span>
      </div>
      <p class="message">{_e(finding.message)}</p>
      <pre class="evidence"><code>{_e(finding.evidence)}</code></pre>
      <div class="fix"><strong>修复建议</strong><p>{_e(finding.remediation)}</p></div>
    </article>
    """


def render_html(result: ScanResult, title: str | None = None) -> str:
    counts = result.counts()
    report_title = title or "SolSentry 扫描报告"
    score = result.risk_score
    grade = result.grade
    grade_colour = {
        "A": "#067647",
        "B": "#067647",
        "C": "#b54708",
        "D": "#d92d20",
        "F": "#b42318",
    }[grade]
    findings = result.sorted_findings()
    findings_html = "\n".join(_finding_html(finding) for finding in findings)
    if not findings:
        findings_html = """
        <div class="empty">
          <strong>未发现匹配规则的风险</strong>
          <p>该目标通过了当前规则集的检查。仍建议结合单元测试、形式化验证与人工审计。</p>
        </div>
        """

    severity_rows = []
    for severity in SEVERITY_ORDER:
        count = counts.get(severity, 0)
        if not count:
            continue
        severity_rows.append(
            f"""
            <div class="dist-row">
              <span class="dist-label"><i style="background:{SEVERITY_COLOURS[severity]}"></i>{_e(SEVERITY_LABELS[severity])}</span>
              <div class="dist-track"><span style="width:{max(3, count * 14)}%;background:{SEVERITY_COLOURS[severity]}"></span></div>
              <strong>{count}</strong>
            </div>
            """
        )
    distribution = "".join(severity_rows) or '<p class="muted">暂无风险项</p>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(report_title)} · SolSentry</title>
<style>
  :root {{
    --ink:#102a33; --muted:#5b7078; --line:#dbe5ea; --bg:#f3f7f8;
    --card:#ffffff; --accent:#0f766e; --accent-2:#14b8a6; --dark:#0b2b33;
    --mono:"Cascadia Code","Consolas","SFMono-Regular",monospace;
    --sans:"Microsoft YaHei","Segoe UI",system-ui,sans-serif;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:14px;line-height:1.65; }}
  .page {{ max-width:1160px;margin:0 auto;padding:28px 28px 56px; }}
  .hero {{ position:relative;overflow:hidden;border-radius:18px;background:linear-gradient(135deg,#09262d 0%,#0f4c4c 58%,#0f766e 100%);color:#fff;padding:30px 34px 26px;box-shadow:0 18px 40px rgba(9,38,45,.18); }}
  .hero:after {{ content:"";position:absolute;right:-60px;top:-80px;width:280px;height:280px;border-radius:50%;background:radial-gradient(circle,rgba(45,212,191,.38),transparent 65%); }}
  .brand {{ display:flex;align-items:center;gap:14px;position:relative;z-index:1; }}
  .logo {{ width:46px;height:46px;border-radius:12px;background:linear-gradient(145deg,#5eead4,#14b8a6);display:grid;place-items:center;color:#062a2a;font:800 26px/1 var(--mono);box-shadow:0 6px 16px rgba(0,0,0,.2); }}
  .brand h1 {{ margin:0;font-size:26px;letter-spacing:.3px; }}
  .brand h1 span {{ font:600 12px/1 var(--mono);color:#99f6e4;background:rgba(255,255,255,.1);padding:4px 7px;border-radius:6px;margin-left:8px;vertical-align:middle; }}
  .brand p {{ margin:2px 0 0;color:#b9dcd9;font-size:12.5px; }}
  .hero-meta {{ display:flex;flex-wrap:wrap;gap:10px 24px;margin-top:22px;position:relative;z-index:1;color:#c7e6e2;font-size:12.5px; }}
  .hero-meta code {{ color:#f0fdfa;background:rgba(255,255,255,.09);padding:2px 7px;border-radius:5px; }}
  .grid {{ display:grid;grid-template-columns:1.25fr 1fr 1.15fr 1fr;gap:14px;margin-top:16px; }}
  .card {{ background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 18px 16px;box-shadow:0 3px 10px rgba(16,42,51,.04); }}
  .card .label {{ color:var(--muted);font-size:12px;letter-spacing:.5px;text-transform:uppercase; }}
  .score-wrap {{ display:flex;align-items:center;gap:16px;margin-top:8px; }}
  .score {{ --value:{score};width:82px;height:82px;border-radius:50%;background:conic-gradient({grade_colour} calc(var(--value)*1%),#e6eef1 0);display:grid;place-items:center;flex:0 0 auto; }}
  .score-inner {{ width:64px;height:64px;border-radius:50%;background:#fff;display:grid;place-items:center;text-align:center; }}
  .score-inner strong {{ display:block;font:700 24px/1 var(--mono);color:{grade_colour}; }}
  .score-inner span {{ font-size:10px;color:var(--muted); }}
  .grade {{ font:800 24px/1 var(--mono);color:{grade_colour}; }}
  .grade-label {{ color:var(--muted);font-size:12px; }}
  .big {{ font:700 30px/1.1 var(--mono);margin-top:10px; }}
  .big small {{ font-size:13px;color:var(--muted);font-family:var(--sans);font-weight:400; }}
  .dist {{ margin-top:10px;display:grid;gap:7px; }}
  .dist-row {{ display:grid;grid-template-columns:58px 1fr 22px;align-items:center;gap:8px;font-size:12px; }}
  .dist-label {{ display:flex;align-items:center;gap:5px;color:var(--muted); }}
  .dist-label i {{ width:7px;height:7px;border-radius:50%;display:inline-block; }}
  .dist-track {{ height:6px;border-radius:99px;background:#edf3f5;overflow:hidden; }}
  .dist-track span {{ display:block;height:100%;border-radius:99px; }}
  .dist-row strong {{ text-align:right;font-family:var(--mono);font-size:12px; }}
  .muted {{ color:var(--muted);font-size:12px;margin:8px 0 0; }}
  .toolbar {{ display:flex;align-items:center;justify-content:space-between;gap:12px;margin:26px 2px 12px; }}
  .toolbar h2 {{ font-size:16px;margin:0;letter-spacing:.2px; }}
  .filters {{ display:flex;gap:6px;flex-wrap:wrap; }}
  .filter {{ border:1px solid var(--line);background:#fff;color:var(--muted);font:12px var(--sans);padding:6px 10px;border-radius:999px;cursor:pointer; }}
  .filter.active {{ background:var(--dark);border-color:var(--dark);color:#fff; }}
  .finding {{ background:var(--card);border:1px solid var(--line);border-left:4px solid var(--severity);border-radius:12px;padding:16px 18px;margin-bottom:12px;box-shadow:0 2px 6px rgba(16,42,51,.03); }}
  .finding.hidden {{ display:none; }}
  .finding-head {{ display:flex;align-items:center;flex-wrap:wrap;gap:8px; }}
  .badge {{ font:700 11px/1 var(--mono);color:#fff;background:var(--severity);padding:5px 7px;border-radius:5px;letter-spacing:.4px; }}
  .rule-id {{ font:600 12px var(--mono);color:var(--severity);background:var(--severity-bg);padding:4px 6px;border-radius:5px; }}
  .finding h2 {{ font-size:15px;margin:0; }}
  .location {{ margin-left:auto;font:12px var(--mono);color:var(--muted);background:#f6f9fa;border:1px solid var(--line);padding:4px 7px;border-radius:6px; }}
  .meta-line {{ display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:9px;color:var(--muted);font-size:12px; }}
  .meta-line code {{ font-family:var(--mono);color:var(--ink); }}
  .message {{ margin:10px 0 10px;color:#203b44; }}
  .evidence {{ margin:0;background:#0b1f24;color:#d7f4ee;border-radius:9px;padding:12px 14px;overflow:auto;font:12.5px/1.6 var(--mono);border:1px solid #163a42; }}
  .fix {{ margin-top:11px;border-top:1px dashed var(--line);padding-top:10px;font-size:13px; }}
  .fix strong {{ color:var(--accent);font-size:12px;letter-spacing:.4px; }}
  .fix p {{ margin:4px 0 0;color:#35525b; }}
  .empty {{ background:#fff;border:1px dashed #bfd5d2;border-radius:12px;padding:28px;text-align:center;color:#245c55; }}
  .empty p {{ margin:6px 0 0;color:var(--muted);font-size:13px; }}
  .footer {{ display:flex;justify-content:space-between;gap:16px;margin-top:28px;padding-top:14px;border-top:1px solid var(--line);color:#7d9299;font-size:11.5px; }}
  @media (max-width:900px) {{ .grid {{ grid-template-columns:1fr 1fr; }} .location {{ margin-left:0; }} }}
  @media print {{ body {{ background:#fff; }} .page {{ max-width:none;padding:0; }} .hero {{ box-shadow:none;border-radius:0; }} .filter {{ display:none; }} .finding {{ break-inside:avoid; }} }}
</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <div class="brand">
      <div class="logo">S</div>
      <div>
        <h1>SolSentry <span>v{_e(__version__)}</span></h1>
        <p>面向 Solidity 的轻量级静态风险扫描器 · 证据优先 · 可解释 · 零依赖</p>
      </div>
    </div>
    <div class="hero-meta">
      <span>目标 <code>{_e(result.target)}</code></span>
      <span>生成时间 {_e(result.generated_at)}</span>
      <span>{result.files_scanned} 个文件 / {result.lines_scanned} 行</span>
      <span>抑制 {result.suppressed} 条</span>
      <span>耗时 {result.elapsed_ms} ms</span>
    </div>
  </header>

  <section class="grid" aria-label="扫描概览">
    <div class="card">
      <div class="label">Risk score</div>
      <div class="score-wrap">
        <div class="score"><div class="score-inner"><strong>{score}</strong><span>/ 100</span></div></div>
        <div>
          <div class="grade">{grade}</div>
          <div class="grade-label">{_e(result.risk_label)}</div>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="label">Findings</div>
      <div class="big">{counts['total']}<small> 个问题</small></div>
      <div class="muted">高危 {counts.get('high', 0)} · 中危 {counts.get('medium', 0)} · 低危 {counts.get('low', 0)}</div>
    </div>
    <div class="card">
      <div class="label">Severity distribution</div>
      <div class="dist">{distribution}</div>
    </div>
    <div class="card">
      <div class="label">Coverage</div>
      <div class="big">{result.lines_scanned}<small> 行已扫描</small></div>
      <div class="muted">{result.files_scanned} 个合约文件 · 7 条规则 · 抑制 {result.suppressed} 条</div>
    </div>
  </section>

  <div class="toolbar">
    <h2>风险明细 <span class="muted">（{counts['total']}）</span></h2>
    <div class="filters" role="group" aria-label="按等级筛选">
      <button class="filter active" data-filter="all">全部</button>
      <button class="filter" data-filter="high">高危</button>
      <button class="filter" data-filter="medium">中危</button>
      <button class="filter" data-filter="low">低危</button>
    </div>
  </div>

  <main id="findings">
    {findings_html}
  </main>

  <footer class="footer">
    <span>SolSentry v{_e(__version__)} · MIT License · 由规则引擎自动生成</span>
    <span>静态分析结果仅供审计参考，不能替代人工复核与运行时验证。</span>
  </footer>
</div>
<script>
  const buttons = document.querySelectorAll('[data-filter]');
  const items = document.querySelectorAll('.finding');
  buttons.forEach(button => {{
    button.addEventListener('click', () => {{
      buttons.forEach(item => item.classList.remove('active'));
      button.classList.add('active');
      const target = button.dataset.filter;
      items.forEach(item => {{
        item.classList.toggle('hidden', target !== 'all' && item.dataset.severity !== target);
      }});
    }});
  }});
</script>
</body>
</html>
"""
