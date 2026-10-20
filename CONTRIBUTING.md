# Contributing to SolSentry

感谢你愿意参与 SolSentry。我们希望这个项目保持**小、清楚、可复核**，所以贡献流程也尽量轻量。

## 先讨论，再动手

- 新规则、扫描行为变化、报告格式变化：请先开 issue，说明目标、样例和误报边界。
- 文档修正、拼写错误、测试补充：可以直接提 PR。
- 安全问题：不要公开开 issue，请按 [SECURITY.md](SECURITY.md) 私下报告。

## 开发环境

只需要 Python 3.10+，不依赖第三方运行时库：

```bash
git clone https://github.com/yaokunliang/solsentry.git
cd solsentry
python -m unittest discover -s tests -v
```

运行扫描器：

```bash
PYTHONPATH=src python -m solsentry scan examples/vulnerable
```

Windows PowerShell：

```powershell
$env:PYTHONPATH = "src"
python -m solsentry scan examples/vulnerable
```

## 分支模型

| 分支 | 用途 | 合并方向 |
| --- | --- | --- |
| `main` | 可发布版本，只接受经过验证的合并 | `release/*` → `main` |
| `develop` | 日常集成 | `feature/*` / `fix/*` → `develop` |
| `feature/<topic>` | 单一功能或规则 | → `develop` |
| `fix/<topic>` | 缺陷修复 | → `develop` 或 `main` |
| `release/<version>` | 发布冻结、版本说明、回归 | → `main`，再回合并 `develop` |

- 功能分支从 `develop` 切出，合并时使用 `--no-ff` 保留合并节点。
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)：
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`。
- 每个 PR 只解决一个 issue；标题使用 `type(scope): summary`。

## 新增规则的验收清单

新增一条规则时，PR 必须包含：

1. `src/solsentry/rules.py` 中的规则元数据（ID、等级、SWC/CWE、说明、修复建议）；
2. `src/solsentry/scanner.py` 中的检测逻辑；
3. `examples/vulnerable/` 下至少一个可命中的样例；
4. `examples/clean/` 下至少一个不应命中的反例；
5. `tests/` 中覆盖命中、未命中、抑制行为的单元测试；
6. `docs/rules.md` 中的检测逻辑、误报边界与参考链接。

## 代码风格

- 使用 4 空格缩进，行宽尽量不超过 100 字符；
- 公开函数写类型标注与简短 docstring；
- 不引入运行时第三方依赖；测试使用 `unittest`；
- 报告文本使用中文，规则 ID、SWC/CWE 使用英文；
- 不提交密钥、真实私钥、真实主网地址或未脱敏的审计报告。

## 评审与合并

- 至少一名维护者完成评审；
- CI（`.github/workflows/ci.yml`）必须通过；
- 评审关注：误报边界、证据是否可定位、测试是否覆盖反例、文档是否同步；
- 合并后删除功能分支；发布分支保留到版本说明归档。

## 行为准则

参与本项目即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
