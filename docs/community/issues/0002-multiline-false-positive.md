# #2 低级调用与 delegatecall 的多行误报

- 状态：closed
- 类型：`type:bug`
- 优先级：`priority:P1`
- 提出：2026-10-02
- 关闭：2026-10-05
- 里程碑：v0.5.0
- 关联 PR：#2

## 复现

```solidity
(bool ok, ) = payable(msg.sender).call{value: amount}("");
require(ok, "transfer failed");
```

该写法已经检查了返回值，但扫描器仍报告 SS-103。另一个误报是：

```solidity
(bool ok, ) = address(this).delegatecall(data);
require(ok);
```

`address(this)` 是静态接收者，不应被 SS-104 标记。

## 讨论

> **维护者**（2026-10-02）
>
> 根因是返回值捕获只看了调用之后的文本，没有回看 `(bool ok, ) =`；
> delegatecall 则错误地检查了参数而不是接收者表达式。

> **评审（自检）**（2026-10-04）
>
> 修复需要同时覆盖三种情况：单行 `bool ok = ...`、元组 `(bool ok, ) = ...`、
> 以及跨行的 `if (!ok)`。每修一种都补一个测试，避免回归。

## 结论

PR #2 合并。新增 4 个测试，误报消除；`examples/clean/BankSafe.sol` 在
`--fail-on high` 下退出码为 0。
