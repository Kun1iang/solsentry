# 使用指南

## 安装

SolSentry 只需要 Python 3.10+，运行时无第三方依赖。

```bash
git clone https://github.com/Kun1iang/solsentry.git
cd solsentry
PYTHONPATH=src python -m solsentry --help
```

安装为命令（可选）：

```bash
python -m pip install .
solsentry --version
```

## 命令

### `scan`

```bash
solsentry scan [路径 ...] [选项]
```

| 选项 | 说明 |
| --- | --- |
| `-f, --format` | `console`（默认）、`json`、`markdown`、`html`、`sarif` |
| `-o, --output` | 写入文件；HTML 未指定时默认 `solsentry-report.html` |
| `--min-severity` | 只展示不低于该等级的问题（默认 `info`） |
| `--fail-on` | 出现不低于该等级的问题时退出码为 1（默认 `high`，可选 `none`） |
| `--exclude` | 排除 glob，可重复；例如 `--exclude "test/**"` |
| `--color` | `auto` / `always` / `never` |
| `--quiet` | 不输出“报告已写入”等提示 |

示例：

```bash
# 终端报告
PYTHONPATH=src python -m solsentry scan contracts/

# JSON，供其他工具消费
PYTHONPATH=src python -m solsentry scan contracts/ -f json -o reports/scan.json

# HTML，归档或展示
PYTHONPATH=src python -m solsentry scan contracts/ -f html -o reports/scan.html

# SARIF，上传到 GitHub Code Scanning
PYTHONPATH=src python -m solsentry scan contracts/ -f sarif -o reports/scan.sarif
```

### `rules`

```bash
solsentry rules
solsentry rules --json
```

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 没有达到 `--fail-on` 阈值的问题 |
| `1` | 存在达到阈值的问题 |
| `2` | 参数错误、路径不存在、没有找到 `.sol` 文件或读取失败 |

CI 中通常使用：

```bash
PYTHONPATH=src python -m solsentry scan contracts/ --fail-on high
```

## 抑制

```solidity
// 只抑制下一行的 SS-103
// solsentry-disable-next-line SS-103
(bool ignored, ) = recipient.call{value: amount}("");

// 抑制当前行
require(tx.origin == owner); // solsentry-disable-line SS-102

// 抑制整个文件中的 SS-105
// solsentry-disable SS-105
```

- 不写规则 ID 时，抑制所有规则；
- 抑制数量会显示在摘要与 HTML 报告中；
- 被抑制的问题不会进入 JSON/SARIF 的 `findings`/`results`，但计数保留。

## 输出格式

### JSON

顶层包含 `tool`、`target`、`generated_at`、`summary`、`findings`、`errors`。
`summary` 中包含各等级数量、风险分、等级、文件/行数、抑制数与耗时。

### SARIF

符合 SARIF 2.1.0。`tool.driver.rules` 包含 7 条规则元数据，`results` 包含
`ruleId`、`level`、`message`、`locations` 与 `partialFingerprints`。
可用于 GitHub Code Scanning、Azure DevOps 等支持 SARIF 的平台。

### HTML

单文件、内联 CSS/JS、无外部字体或图片依赖。包含：

- 风险分与 A–F 等级；
- 高危/中危/低危分布；
- 按等级筛选；
- 每条发现的源码证据与修复建议。

## 在 CI 中使用

```yaml
name: security

on: [push, pull_request]

jobs:
  solsentry:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Run tests
        run: python -m unittest discover -s tests -v
      - name: Scan contracts
        run: |
          PYTHONPATH=src python -m solsentry scan contracts/ \
            --format sarif --output solsentry.sarif --fail-on high
      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: solsentry.sarif
```

## 已知限制

- 不解析继承与内联汇编；
- 不执行合约，不做 PoC；
- 规则是启发式匹配，必须人工复核；
- 对超大文件或深层嵌套的性能未做基准测试。

完整规则说明见 [rules.md](rules.md)，架构见 [architecture.md](architecture.md)。
