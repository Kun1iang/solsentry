# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与
[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-11-08

### Added

- 7 条静态规则：重入、`tx.origin`、低级调用未检查、动态 `delegatecall`、
  弱随机数、`selfdestruct`、敏感函数缺权限。
- `scan` / `rules` 两个 CLI 子命令，支持 `--fail-on` 与 `--min-severity`。
- 终端、JSON、Markdown、HTML、SARIF 2.1.0 五种输出。
- 独立 HTML 报告：风险分、等级分布、按等级筛选、源码证据与修复建议。
- `solsentry-disable-next-line` / `-line` / 文件级抑制注释。
- 30 个 `unittest` 用例，覆盖规则、抑制、CLI 与报告。
- GitHub Actions CI（Python 3.10 / 3.11 / 3.12）。
- 完整社区文档：贡献指南、行为准则、安全策略、issue/PR 模板。

### Changed

- 风险分权重调整为 critical=30、high=12、medium=4、low=1，避免单一问题直接顶满。
- HTML 报告改为单文件、无外部资源，便于归档与 CI artifact。

### Fixed

- 修复多行 `.call{value: ...}` 被误判为未检查返回值的问题。
- 修复 `address(this).delegatecall(...)` 被误报为动态目标的问题。
- 修复 SARIF `ruleIndex` 与 `ruleId` 不一致的问题。

## [0.5.0] - 2026-10-20

### Added

- HTML 报告原型与风险评分。
- `examples/vulnerable`、`examples/clean` 样例库。
- 规则文档初稿。

## [0.1.0] - 2026-09-26

### Added

- 项目初始化：文件发现、函数切片、基础规则框架。
- MIT 许可证、README 与第一版测试。
