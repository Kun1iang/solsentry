# PR #1 feat: 规则引擎与首批规则

- 状态：merged
- 作者：姚坤良
- 评审：维护者自检 + 自动检查
- 合并：2026-09-26
- 关联 issue：#1
- 目标分支：`develop`

## 变更

- 新增文件发现、注释剥离、函数切片与状态变量收集；
- 实现 SS-101、SS-102、SS-103；
- 新增 3 个 vulnerable 合约与 2 个 clean 合约；
- 新增 `tests/test_scanner.py`。

## 评审意见

- `tx.origin` 规则只报一次/函数，避免同一行多次命中；
- 重入规则要跳过带 `nonReentrant` 的函数；
- 证据行必须来自原始源码，不能用剥离注释后的文本。

## 验证

```text
$ python -m unittest discover -s tests -v
Ran 12 tests in 0.4s
OK
```

## 合并后

`--no-ff` 合并到 `develop`；删除 `feature/rule-engine`。
