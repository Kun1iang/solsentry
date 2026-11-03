<p align="center">
  <img src="docs/assets/brand/solsentry-mark.svg" width="96" alt="SolSentry logo">
</p>

<h1 align="center">SolSentry</h1>

<p align="center">
  <strong>面向 Solidity 的轻量级静态风险扫描器</strong><br>
  证据优先 · 可解释 · 零运行时依赖 · 适合 CI
</p>

<p align="center">
  <img src="docs/assets/badges/version.svg" alt="version">
  <img src="docs/assets/badges/tests.svg" alt="tests">
  <img src="docs/assets/badges/python.svg" alt="python">
  <img src="docs/assets/badges/license.svg" alt="license">
</p>

---

## 为什么做 SolSentry

智能合约漏洞的代价极高，但很多团队在 CI 里仍缺少一个**足够轻、输出足够可读**的第一道检查。
重量级分析平台学习成本高、报告术语密集；通用大模型又可能给出无法定位的结论。
SolSentry 选择另一条路：

- **规则少而明确**：只覆盖 7 类高信号风险，每条都能落到 `文件:行:列`；
- **证据可复核**：报告保留命中的源码行、SWC/CWE 映射、置信度和修复建议；
- **零运行时依赖**：只使用 Python 标准库，Windows / Linux / macOS 开箱即用；
- **对 CI 友好**：支持 JSON、Markdown、SARIF 与独立 HTML 报告，可用退出码阻断高危合并。

本项目同时是本科毕业设计《基于多智能体与静态分析协同的智能合约漏洞检测及修复建议平台》的
**静态分析证据层**开源组件。它负责把“可疑代码位置 + 依据”稳定地交给上层审计智能体，
再由智能体完成复现、修复与回归；本项目本身不调用大模型，也不替代人工审计。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 7 条内置规则 | 重入、`tx.origin`、低级调用未检查、动态 `delegatecall`、弱随机数、`selfdestruct`、敏感函数缺权限 |
| 行级证据 | 每条发现都包含文件、行、列、函数、源码行与修复建议 |
| 多种报告 | 终端、JSON、Markdown、SARIF 2.1.0、独立 HTML（含等级筛选） |
| 抑制注释 | `solsentry-disable-next-line` / `-line` / 文件级，方便对已确认项留痕 |
| 风险评分 | 按等级加权得到 0–100 分与 A–F 等级，便于趋势对比 |
| 零依赖 | Python 3.10+ 标准库即可运行；测试也不依赖 pytest |

## 快速开始

```powershell
git clone https://github.com/yaokunliang/solsentry.git
cd solsentry

# 不安装包也可以直接运行
$env:PYTHONPATH = "src"
python -m solsentry scan examples/vulnerable
```

Linux / macOS：

```bash
git clone https://github.com/yaokunliang/solsentry.git
cd solsentry
PYTHONPATH=src python -m solsentry scan examples/vulnerable
```

可选安装为命令：

```bash
python -m pip install .
solsentry scan contracts/
```

### 一次真实扫描

```text
$ python -m solsentry scan examples/vulnerable
SolSentry v1.0.0  ·  Solidity 静态风险扫描器
目标: examples/vulnerable
扫描: 3 个文件 / 101 行  ·  用时 5 ms

[HIGH] SS-101  Reentrancy  examples/vulnerable/Bank.sol:20:33
  函数: withdraw  ·  等级: 高危  ·  SWC-107 / CWE-841
  证据: (bool ok, ) = msg.sender.call{value: amount}("");
  说明: 函数 withdraw 在外部调用后仍更新状态变量 balances，存在重入窗口。
  修复: 遵循 Checks-Effects-Interactions：先更新状态，再进行外部调用……

结果: 11 个问题（5 高危 / 6 中危）  ·  风险分 84/100 (F)  ·  抑制 0 条
```

### 生成 HTML 报告

```bash
python -m solsentry scan examples/vulnerable \
  --format html \
  --output docs/assets/scan-report.html
```

报告是单文件、无外部资源，可直接归档或上传为 CI artifact。

### 接入 CI

```yaml
- name: SolSentry
  run: |
    PYTHONPATH=src python -m solsentry scan contracts \
      --format sarif \
      --output solsentry.sarif \
      --fail-on high
```

`--fail-on high` 会在出现高危及以上问题时返回退出码 `1`，从而阻断合并。

## 规则集

| ID | 风险 | SWC | CWE | 检测要点 |
| --- | --- | --- | --- | --- |
| SS-101 | 重入 | SWC-107 | CWE-841 | 外部调用之后仍写入状态变量，且函数没有 `nonReentrant` |
| SS-102 | 身份校验 | SWC-115 | CWE-284 | 在权限判断中使用 `tx.origin` |
| SS-103 | 低级调用 | SWC-104 | CWE-252 | `.call` / `.send` 的返回值未被 `require` 或条件检查 |
| SS-104 | 动态委托 | SWC-112 | CWE-829 | `delegatecall` 的接收者是参数或可变状态，而非字面量/常量 |
| SS-105 | 弱随机 | SWC-120 | CWE-330 | 用 `block.timestamp` / `blockhash` 参与随机数计算 |
| SS-106 | 自毁 | SWC-106 | CWE-284 | 调用 `selfdestruct` / `suicide` |
| SS-107 | 权限缺失 | SWC-105 | CWE-284 | 敏感管理函数为 public/external 且未见权限校验 |

完整检测逻辑、误报边界与修复范式见 [docs/rules.md](docs/rules.md)。

## 设计原则

1. **先证据，后结论**：没有源码行与位置的发现不进入报告。
2. **宁可少报，不要瞎报**：规则只做高信号匹配，置信度低时显式标记。
3. **可抑制，可复核**：允许开发者对确认项写抑制注释，但报告保留抑制计数。
4. **小核心，可扩展**：扫描器、规则元数据、报告器分离，新增规则只需注册元数据与检测函数。

```text
Solidity files
      │
      ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 文件发现/读取 │ →  │ 轻量语法切片  │ →  │  规则匹配     │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
              Console / JSON              Markdown / HTML              SARIF 2.1.0
```

## 项目结构

```text
solsentry/
├─ src/solsentry/          # 扫描器、规则元数据、报告器、CLI
├─ tests/                  # 30 个 unittest 用例（含 CLI 与报告）
├─ examples/
│  ├─ vulnerable/          # 3 个故意不安全的合约
│  └─ clean/               # 2 个通过检查的参考实现
├─ docs/
│  ├─ rules.md             # 规则说明与误报边界
│  ├─ architecture.md      # 架构与扩展点
│  ├─ usage.md             # CLI、退出码、抑制、CI
│  ├─ community/           # issue / PR / 决策记录
│  └─ releases/            # 版本说明
├─ .github/                # issue 模板、PR 模板、CI
├─ CONTRIBUTING.md
├─ CODE_OF_CONDUCT.md
├─ SECURITY.md
├─ CHANGELOG.md
└─ LICENSE
```

## 分支模型

项目采用简化 Git Flow：

- `main`：可发布、带标签的稳定分支；
- `develop`：集成分支，功能合并前先通过本地测试；
- `feature/*`：单一职责的功能分支；
- `fix/*`：缺陷修复；
- `release/*`：发布冻结与发布说明。

每次合并使用 `--no-ff` 保留合并节点；提交信息遵循 Conventional Commits。
详细流程见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [docs/community.md](docs/community.md)。

## 参与贡献

欢迎提交 issue 与 pull request：

- 新规则需要同时提供 **vulnerable 样例 + clean 反例 + 单元测试**；
- 修改扫描逻辑必须保持现有 30 个测试通过；
- PR 必须关联 issue，并在描述中说明误报边界；
- 行为准则见 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 许可证

本项目使用 [MIT License](LICENSE)。你可以自由使用、修改、分发，但需保留版权与许可声明。
第三方参考（SWC Registry、OpenZeppelin、Slither）仅作为规则设计与文档引用，未复制其代码。

## 参考

- [SWC Registry](https://swcregistry.io/)
- [MITRE CWE](https://cwe.mitre.org/)
- [Solidity Security Considerations](https://docs.soliditylang.org/en/latest/security-considerations.html)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Slither](https://github.com/crytic/slither)

---

<p align="center">
  <sub>SolSentry v1.0.0 · 用可复核的证据，让合约审计从第一行代码开始。</sub>
</p>
