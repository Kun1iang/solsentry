# #4 SARIF `ruleIndex` 与 `ruleId` 不一致

- 状态：closed
- 类型：`type:bug`
- 优先级：`priority:P1`
- 提出：2026-10-24
- 关闭：2026-10-27
- 里程碑：v1.0.0
- 关联 PR：#4

## 复现

运行：

```bash
python -m solsentry scan examples/vulnerable --format sarif > out.sarif
```

用 SARIF 查看器打开后，部分结果的 `ruleIndex` 指向了错误规则，
导致规则描述和实际发现不匹配。

## 讨论

> **维护者**（2026-10-24）
>
> 当前 `ruleIndex` 是按发现顺序计算的，应该用 `RULES` 的固定顺序建立映射。
> 同时补充 SARIF 结构测试，防止后续新增规则时再次错位。

> **评审（自检）**（2026-10-26）
>
> 还要检查 `artifacts` 是否去重、`level` 映射是否符合 SARIF 约定：
> high/critical → error，medium → warning，low/info → note。

## 结论

PR #4 合并。SARIF 输出通过 JSON 结构测试，并加入 `docs/usage.md` 的
GitHub Code Scanning 示例。
