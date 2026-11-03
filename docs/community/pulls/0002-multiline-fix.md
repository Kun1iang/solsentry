# PR #2 fix: 多行调用误报与委托接收者判断

- 状态：merged
- 作者：姚坤良
- 评审：维护者自检 + 自动检查
- 合并：2026-10-05
- 关联 issue：#2
- 目标分支：`develop`

## 变更

- `_superseded_by_check()` 回看 `(bool ok, ) =` 与 `bool ok =` 两种捕获；
- 检查 `require(ok)`、`if (!ok)`、`assert(ok)` 等消费方式；
- SS-104 改为检查 `delegatecall` 的接收者表达式，而不是参数；
- 新增 4 个回归测试。

## 评审意见

- 不能把 `sent;` 这种“只引用不检查”误判为已检查；
- `address(this)`、`this`、`0x...` 与全大写常量名视为静态接收者；
- 仍然保留对 `implementation.delegatecall` 等高危模式的告警。

## 验证

```text
$ python -m unittest discover -s tests -v
Ran 16 tests in 0.6s
OK
```

## 合并后

合并到 `develop`；`examples/clean/BankSafe.sol` 通过检查。
