# PR #4 feat: SARIF 2.1.0 输出

- 状态：merged
- 作者：姚坤良
- 评审：维护者自检 + 自动检查
- 合并：2026-10-27
- 关联 issue：#4
- 目标分支：`develop`

## 变更

- 新增 `render_sarif()`；
- `ruleIndex` 使用 `RULES` 固定顺序映射；
- `level` 映射：high/critical → error，medium → warning，low/info → note；
- CLI 增加 `--format sarif`；
- 新增 SARIF 结构测试与 GitHub Code Scanning 示例。

## 评审意见

- `$schema` 与 `version` 必须同时存在；
- `artifacts` 去重并按路径排序；
- `partialFingerprints` 使用规则 + 文件 + 行，便于平台去重；
- `executionSuccessful` 与 `errors` 保持一致。

## 验证

```text
$ python -m unittest discover -s tests -v
Ran 26 tests in 1.4s
OK
```

## 合并后

合并到 `develop`；SARIF 示例保留在 `docs/assets/scan-report.sarif`。
