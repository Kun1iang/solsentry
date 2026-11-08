# 架构

## 目标

SolSentry 的目标不是“发现所有漏洞”，而是为开发者与上层审计智能体提供一个
**稳定、可解释、可接入 CI** 的静态证据层：

1. 输入 Solidity 文件，输出带 `文件:行:列` 的风险线索；
2. 每条线索都包含规则 ID、等级、证据、说明与修复建议；
3. 结果可以序列化为 JSON / SARIF，供其他系统消费；
4. 运行环境尽量简单：Python 3.10+，零运行时依赖。

## 数据流

```text
CLI (scan)
   │
   ▼
文件发现 ──► 读取/解码 ──► 注释剥离 ──► 函数切片 ──► 状态变量收集
                                                   │
                                                   ▼
                                        规则匹配（7 条）
                                                   │
                                                   ▼
                                     抑制过滤 ──► 排序/去重
                                                   │
                    ┌──────────────┬───────────────┼──────────────┬──────────────┐
                    ▼              ▼               ▼              ▼              ▼
                 Console         JSON          Markdown          HTML           SARIF
```

## 模块

| 模块 | 职责 |
| --- | --- |
| `src/solsentry/scanner.py` | 文件发现、注释剥离、函数切片、规则实现、抑制过滤 |
| `src/solsentry/rules.py` | 规则元数据：ID、等级、SWC/CWE、说明、修复建议 |
| `src/solsentry/models.py` | `Finding` / `ScanResult`、风险评分与等级 |
| `src/solsentry/report.py` | 五种输出格式的渲染 |
| `src/solsentry/cli.py` | 参数解析、输出写入、退出码 |
| `tests/` | 规则命中/未命中、抑制、CLI、SARIF/HTML 结构 |
| `examples/` | 可复现的 vulnerable / clean 合约 |

## 关键设计

### 1. 轻量语法切片，而不是完整 AST

扫描器先用一个小型状态机剥离注释（保留换行与偏移），再用正则找到函数头，
通过花括号配对得到函数体。它不构建完整 AST，因此：

- 优点是零依赖、启动快、易于在 Windows 上运行；
- 缺点是无法精确处理继承、内联汇编、复杂表达式；
- 因此规则输出带置信度，并明确“待人工复核”。

### 2. 规则与报告分离

规则只产生 `Finding`，报告器只消费 `ScanResult`。新增输出格式不需要改规则；
新增规则也不需要改 CLI。这样可以让“检测”和“呈现”各自演进。

### 3. 证据优先

`Finding` 必须带 `file`、`line`、`column`、`function`、`evidence`。
没有源码位置的线索不会进入结果。这是为了满足审计场景的可复核性：
评审者可以立即跳转到对应行，而不是相信一句自然语言结论。

### 4. 抑制是显式的

```solidity
// solsentry-disable-next-line SS-103
(bool ignored, ) = recipient.call{value: amount}("");
```

抑制不会删除发现，而是在 `ScanResult.suppressed` 中计数，报告仍显示“抑制 N 条”。
这样既尊重开发者的判断，也保留审计痕迹。

### 5. 风险分是趋势指标，不是结论

风险分按等级加权（critical=30、high=12、medium=4、low=1，封顶 100），
用于比较同一项目不同提交的趋势。它不能替代人工审计，也不应单独作为上线依据。

## 扩展点

### 新增规则

1. 在 `rules.py` 注册 `Rule`；
2. 在 `Scanner` 增加检测方法，或在现有方法中增加模式；
3. 在 `examples/` 添加 vulnerable/clean 样例；
4. 在 `tests/` 覆盖命中、未命中、抑制；
5. 在 `docs/rules.md` 写清检测逻辑与误报边界。

### 新增报告格式

1. 在 `report.py` 增加 `render_xxx(result)`；
2. 在 `cli.py` 的 `--format` 与 `_render` 注册；
3. 增加结构测试；
4. 更新 `docs/usage.md`。

### 与毕设平台的集成

毕设平台的多智能体审计链路可以把 SolSentry 作为“静态分析工具”节点：

```text
编排 Agent
   ├─ 调用 SolSentry（JSON/SARIF）→ 得到候选位置与证据
   ├─ 知识检索 Agent → 补充 SWC/CWE 与修复范式
   ├─ 验证 Agent → 生成 Foundry PoC 并执行
   └─ 修复 Agent → 生成 patch 并回归
```

SolSentry 不调用大模型，也不做 PoC 执行；它只负责把“哪里可疑、为什么可疑”
稳定地交给上层，从而降低大模型幻觉对审计结论的影响。

## 非目标

- 不做形式化验证或符号执行；
- 不执行合约、不连接链、不处理私钥；
- 不替代人工审计、运行时监控或经济模型分析；
- 不追求覆盖所有 SWC 类别，只维护高信号子集。
