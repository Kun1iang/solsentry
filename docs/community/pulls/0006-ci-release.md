# PR #6 chore: CI 矩阵与 v1.0.0 发布准备

- 状态：merged
- 作者：姚坤良
- 评审：维护者自检 + 自动检查
- 合并：2026-11-06
- 关联 issue：#7、#8
- 目标分支：`release/v1.0.0`

## 变更

- GitHub Actions 矩阵：Python 3.10 / 3.11 / 3.12；
- 增加 `compileall`、单元测试、示例扫描；
- 更新 CHANGELOG 与 `docs/releases/v1.0.0.md`；
- 版本号更新为 1.0.0；
- 增加 release 检查清单。

## 评审意见

- 示例扫描预期退出码为 1，CI 中显式允许；
- 不在 CI 中安装第三方 lint 工具，保持零依赖；
- release 分支只接受修复和文档；
- 合并后打 annotated tag `v1.0.0`。

## 验证

```text
$ python -m unittest discover -s tests -v
Ran 30 tests in 2.0s
OK

$ PYTHONPATH=src python -m solsentry scan examples/clean --fail-on high
exit code 0
```

## 合并后

合并到 `main`，打 tag `v1.0.0`；回合并 `develop`。
