# PR #5 docs: 规则说明、贡献指南与抑制注释

- 状态：merged
- 作者：姚坤良
- 评审：维护者自检 + 自动检查
- 合并：2026-11-03
- 关联 issue：#5、#6
- 目标分支：`develop`

## 变更

- 完成 `docs/rules.md` 的 7 条规则说明；
- 新增 `CONTRIBUTING.md`、`CODE_OF_CONDUCT.md`、`SECURITY.md`；
- 实现 `solsentry-disable-next-line` / `-line` / 文件级抑制；
- 新增 3 个抑制测试；
- 更新 README 的规则表与限制说明。

## 评审意见

- 文档中的规则 ID、SWC/CWE 必须与 `rules.py` 一致；
- 抑制注释不改变行号，避免报告位置漂移；
- 抑制计数进入 JSON 与 HTML 摘要；
- 贡献指南必须要求 vulnerable + clean 双样例。

## 验证

```text
$ python -m unittest discover -s tests -v
Ran 30 tests in 1.8s
OK
```

## 合并后

合并到 `develop`；准备 v1.0.0 发布。
