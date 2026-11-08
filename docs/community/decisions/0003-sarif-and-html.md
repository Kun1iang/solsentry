# ADR-0003：同时提供 SARIF 与独立 HTML

- 状态：accepted
- 日期：2026-10-25
- 决策者：维护者

## 背景

不同消费者需要不同格式：

- CI / 代码扫描平台需要机器可读的 SARIF；
- 课程报告、审计归档需要人类可读、可截图的 HTML；
- 其他脚本可能只需要 JSON。

如果只做一种格式，会迫使下游写转换器。

## 决策

同时提供：

- `json`：稳定的自有结构，便于二次开发；
- `sarif`：符合 SARIF 2.1.0，可上传代码扫描平台；
- `html`：单文件、无外部资源、可离线打开；
- `markdown`：适合粘贴到 issue/PR；
- `console`：开发时的快速反馈。

## 理由

- 渲染层与扫描层分离，新增格式不影响规则；
- HTML 与 SARIF 共享同一 `ScanResult`，避免两套数据口径；
- SARIF 的 `ruleIndex` 使用固定规则顺序，保证稳定；
- HTML 转义所有源码证据，避免注入。

## 代价

- 需要维护多种渲染器与对应测试；
- HTML 的视觉设计需要额外投入；
- SARIF 字段较多，容易漏字段，需要结构测试。

## 结果

- `report.py` 包含 5 个渲染函数；
- `test_reports.py` 覆盖 JSON、Markdown、SARIF、HTML；
- `docs/usage.md` 给出 CI 与 Code Scanning 示例。
