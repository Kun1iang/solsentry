# 社区协作与治理

SolSentry_28 目前处于课程项目孵化阶段。仓库已经按真实开源项目的协作方式配置：
issue 模板、PR 模板、标签体系、评审清单、发布流程与行为准则都已落地。
本节记录协作机制、里程碑和首次协作闭环，**不虚构外部 star/fork 或陌生人贡献**。

## 角色

| 角色 | 职责 |
| --- | --- |
| Maintainer（维护者） | 规划路线、分配标签、评审 PR、合并与发布、执行行为准则 |
| Reviewer（评审者） | 检查规则误报边界、测试覆盖、文档同步与安全影响 |
| Contributor（贡献者） | 提交 issue/PR、补充样例与测试、改进文档 |

课程阶段由作者担任 Maintainer，并采用“作者自评审 + 自动化检查”的轻量评审；
外部贡献者加入后，按同一清单执行。

## 标签体系

| 标签 | 含义 |
| --- | --- |
| `type:feature` | 新功能/新规则 |
| `type:bug` | 缺陷或误报 |
| `type:docs` | 文档改进 |
| `type:chore` | CI、构建、发布等 |
| `rule:SS-101` … `rule:SS-107` | 关联具体规则 |
| `priority:P0/P1/P2` | 阻断发布 / 本迭代 / 可延后 |
| `status:review` | 等待评审 |
| `good first issue` | 适合首次贡献 |

## Issue 流程

1. 使用模板描述背景、复现、期望行为与影响范围；
2. 维护者在 72 小时内打标签、定优先级、决定是否进入里程碑；
3. 能复现的问题附最小合约片段；规则问题必须附 vulnerable/clean 样例；
4. 关闭时关联 PR 或提交，并在 issue 中留下结论。

## PR 流程

```text
issue → feature/fix 分支 → 本地测试 → PR（关联 issue）
      → CI 通过 → 评审清单 → --no-ff 合并 → 删除分支
```

评审清单：

- [ ] 变更是否只解决一个 issue？
- [ ] 新规则是否有 vulnerable 命中样例与 clean 反例？
- [ ] 是否覆盖抑制行为与边界条件？
- [ ] 报告输出是否仍可解析（JSON/SARIF）？
- [ ] 文档（rules/usage/CHANGELOG）是否同步？
- [ ] 是否引入运行时第三方依赖？
- [ ] 是否包含密钥、真实地址或未脱敏数据？

## 里程碑与发布

| 版本 | 日期 | 内容 | 状态 |
| --- | --- | --- | --- |
| v0.1.0 | 2026-09-26 | 扫描骨架、首批规则、样例库 | released |
| v0.5.0 | 2026-10-20 | HTML 报告、风险评分、规则文档 | released |
| v1.0.0 | 2026-11-08 | SARIF、抑制、CI 矩阵、社区文档 | released |

发布流程：

1. 从 `develop` 切出 `release/<version>`；
2. 冻结功能，只接受修复与文档；
3. 更新 `CHANGELOG.md`、`docs/releases/<version>.md` 与版本号；
4. 跑全量测试与示例扫描；
5. `--no-ff` 合并到 `main`，打 annotated tag；
6. 回合并 `develop`，删除 release 分支。

## 协作记录（课程阶段）

| 指标 | 数值 |
| --- | ---: |
| Issue 开启 / 关闭 | 8 / 8 |
| Pull Request 合并 | 6 |
| 发布版本 | 3 |
| 设计决策记录（ADR） | 3 |
| 单元测试 | 30 |
| 外部贡献者 | 0（课程孵化阶段，欢迎首位贡献者） |

### Issue 索引

| # | 标题 | 类型 | 状态 | 关联 PR |
| --- | --- | --- | --- | --- |
| #1 | 初始化规则引擎与样例库 | feature | closed | #1 |
| #2 | 低级调用与 delegatecall 的多行误报 | bug | closed | #2 |
| #3 | 增加独立 HTML 报告 | feature | closed | #3 |
| #4 | SARIF `ruleIndex` 与 `ruleId` 不一致 | bug | closed | #4 |
| #5 | 规则文档缺少 SWC/CWE 对照 | docs | closed | #5 |
| #6 | 支持行内抑制注释 | feature | closed | #5 |
| #7 | CI 增加 Python 3.12 矩阵 | chore | closed | #6 |
| #8 | v1.0.0 发布检查清单 | release | closed | #6 |

### Pull Request 索引

| PR | 标题 | 变更范围 | 评审结论 |
| --- | --- | --- | --- |
| #1 | feat: 规则引擎与首批规则 | scanner、examples、tests | 合并 |
| #2 | fix: 多行调用误报与委托接收者判断 | scanner、tests | 合并 |
| #3 | feat: 独立 HTML 报告与风险评分 | report、docs/assets | 合并 |
| #4 | feat: SARIF 2.1.0 输出 | report、cli、tests | 合并 |
| #5 | docs: 规则说明、贡献指南与抑制注释 | docs、tests | 合并 |
| #6 | chore: CI 矩阵与 v1.0.0 发布准备 | CI、CHANGELOG、release | 合并 |

详细记录见 [`docs/community/issues/`](community/issues/) 与
[`docs/community/pulls/`](community/pulls/)。

## 诚实的边界

- 本阶段没有外部用户，因此没有 star/fork/外部 issue 数据；
- 所有协作记录来自课程开发过程，评审以“维护者自检 + 自动化检查”完成；
- 报告展示的是**可运行的协作机制与真实的开发闭环**，不是伪造的社区热度；
- 项目发布到公共平台后，可按同一流程接收外部贡献，并在此追加指标。
