# #6 支持行内抑制注释

- 状态：closed
- 类型：`type:feature`
- 优先级：`priority:P1`
- 提出：2026-10-30
- 关闭：2026-11-03
- 里程碑：v1.0.0
- 关联 PR：#5

## 背景

审计中会确认“这个低级调用失败可以忽略”或“这是测试合约的故意漏洞”。
如果只能改规则或忽略整个文件，会丢失审计痕迹。

## 期望

```solidity
// solsentry-disable-next-line SS-103
(bool ignored, ) = recipient.call{value: amount}("");

require(tx.origin == owner); // solsentry-disable-line SS-102

// solsentry-disable SS-105
```

被抑制的发现不进入结果，但要在摘要中计数，报告中保留“抑制 N 条”。

## 讨论

> **维护者**（2026-10-30）
>
> 只做注释形式，不做配置文件；配置文件容易在 CI 中丢失上下文。
> 抑制必须写规则 ID，除非明确要抑制全部。

> **评审（自检）**（2026-11-02）
>
> 要覆盖“下一行”“当前行”“文件级”三种作用域，并确保行号偏移不受注释剥离影响。

## 结论

PR #5 合并。新增 3 个抑制测试，`ScanResult.suppressed` 进入 JSON/HTML 摘要。
