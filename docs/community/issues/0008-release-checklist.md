# #8 v1.0.0 发布检查清单

- 状态：closed
- 类型：`type:release`
- 优先级：`priority:P0`
- 提出：2026-11-07
- 关闭：2026-11-08
- 里程碑：v1.0.0
- 关联 PR：#6

## 检查项

- [x] 7 条规则均有文档与样例
- [x] 30 个单元测试通过（Python 3.10/3.11/3.12）
- [x] `examples/clean` 退出码 0，`examples/vulnerable` 退出码 1
- [x] JSON / SARIF 结构测试通过
- [x] HTML 报告无外部资源
- [x] CHANGELOG 与 release notes 同步
- [x] LICENSE、CONTRIBUTING、CODE_OF_CONDUCT、SECURITY 齐全
- [x] 分支 `release/v1.0.0` 合并回 `main` 并打 tag

## 讨论

> **维护者**（2026-11-07）
>
> 版本号从 0.5.0 直接到 1.0.0，因为 CLI、报告格式与规则 ID 已稳定；
> 后续不兼容变更走 2.0.0。

## 结论

2026-11-08 发布 v1.0.0，annotated tag 指向 release 合并提交。
