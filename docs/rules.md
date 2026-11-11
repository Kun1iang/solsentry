# 规则说明

SolSentry_28 目前内置 7 条规则。它们不是完整的形式化验证，而是**高信号、可定位、可解释**的
第一道检查。每条规则都给出检测逻辑、误报边界和修复建议，方便评审者判断结果是否成立。

> 风险等级：`critical` > `high` > `medium` > `low` > `info`。  
> 置信度：`high` 表示模式明确；`medium` 表示需要结合上下文；`low` 表示启发式提示，必须人工复核。

## 总览

| ID | 名称 | 等级 | 置信度 | SWC | CWE |
| --- | --- | --- | --- | --- | --- |
| SS-101 | Reentrancy | high | medium | SWC-107 | CWE-841 |
| SS-102 | tx.origin Authentication | high | high | SWC-115 | CWE-284 |
| SS-103 | Unchecked Low-Level Call | medium | medium | SWC-104 | CWE-252 |
| SS-104 | Delegatecall to Dynamic Target | high | high | SWC-112 | CWE-829 |
| SS-105 | Weak On-Chain Randomness | medium | medium | SWC-120 | CWE-330 |
| SS-106 | Selfdestruct Usage | high | high | SWC-106 | CWE-284 |
| SS-107 | Missing Access Control | medium | low | SWC-105 | CWE-284 |

---

## SS-101 Reentrancy

**检测逻辑**：在同一个函数体内，先出现 `.call{...}(...)` 或 `.send(...)` 外部调用，
之后又出现对合约级状态变量的赋值/复合赋值/`delete`，且函数头没有 `nonReentrant` 修饰符。

**为什么危险**：攻击者在外部调用期间重入函数，此时状态尚未更新，可重复提款或破坏账本。

**误报边界**：

- 状态更新发生在外部调用之前（Checks-Effects-Interactions）→ 不报；
- 函数有 `nonReentrant` → 不报；
- 只调用 `transfer` / `send` 且状态更新在前 → 当前不报（`transfer` 不在外部调用模式中）；
- 跨函数重入、跨合约回调、复杂控制流 → 当前版本可能漏报，需要人工审计。

**修复**：先扣减余额、再转账；或使用 `nonReentrant`；补充重入测试。

**参考**：<https://swcregistry.io/docs/SWC-107>

---

## SS-102 tx.origin Authentication

**检测逻辑**：函数体内出现 `tx.origin`。

**为什么危险**：`tx.origin` 是交易的最初发起者，而不是当前调用者。钓鱼合约可诱导受害者
调用，从而以受害者身份通过校验。

**误报边界**：仅用于日志、事件或非安全判断时，风险较低；规则仍会报告，建议人工确认。

**修复**：改用 `msg.sender`；元交易场景使用 EIP-2771 可信转发器并校验转发器地址。

**参考**：<https://swcregistry.io/docs/SWC-115>

---

## SS-103 Unchecked Low-Level Call

**检测逻辑**：匹配 `.call(...)` / `.send(...)`；若返回值没有被 `bool` 变量捕获，
或捕获后没有 `require` / `if` / `assert` 检查，则报告。

**为什么危险**：低级调用失败不会自动回滚，未检查返回值会让合约继续执行，造成状态不一致。

**误报边界**：

- `(bool ok, ) = target.call(...); require(ok);` → 不报；
- 故意忽略失败（例如“尽力转账”）→ 需要写抑制注释并在文档说明；
- 通过 `try/catch` 包装的外部调用 → 当前不覆盖。

**修复**：检查返回值；优先使用经过审计的转账库；对失败路径写测试。

**参考**：<https://swcregistry.io/docs/SWC-104>

---

## SS-104 Delegatecall to Dynamic Target

**检测逻辑**：匹配 `X.delegatecall(...)`；若接收者 `X` 不是 `address(this)`、`this`、
十六进制地址字面量或全大写常量名，则报告。

**为什么危险**：`delegatecall` 在调用者上下文中执行，攻击者控制目标后可改写存储、
窃取权限或转走资金。

**误报边界**：

- 目标来自不可变常量、EIP-1967 槽位且升级入口有权限控制 → 仍需人工确认；
- 代理模式中的 `address(this).delegatecall` 不在本规则范围；
- 内联汇编中的 `delegatecall` 当前不解析。

**修复**：目标地址不可变化或受权限控制；升级入口加 `onlyOwner`/`onlyRole`；
校验实现代码哈希；使用成熟代理库。

**参考**：<https://swcregistry.io/docs/SWC-112>

---

## SS-105 Weak On-Chain Randomness

**检测逻辑**：函数体内同一行出现 `block.timestamp`、`block.number`、`blockhash`、
`block.prevrandao` 等链上可观测值，并且同一行包含 `%`、`keccak256`、`sha256`、
`rand`、`seed`、`winner`、`lottery` 等随机语义。

**为什么危险**：验证者可以观察甚至影响区块变量，抽奖、铸造、分配等结果可被预测或操纵。

**误报边界**：仅用于时间锁、截止时间判断时不报；用于非资金场景时仍建议写抑制注释并说明。

**修复**：使用 Chainlink VRF 等可验证随机函数；将随机性与资金逻辑隔离。

**参考**：<https://swcregistry.io/docs/SWC-120>

---

## SS-106 Selfdestruct Usage

**检测逻辑**：匹配 `selfdestruct(...)` 或 `suicide(...)`。

**为什么危险**：`selfdestruct` 强制转移余额并删除代码；上海升级后语义变化，
代理、审计假设和资金安全都可能被破坏。

**修复**：移除自毁；改用 `pause` + 受控 `withdraw` 的下架流程；如必须保留，加权限、
事件与迁移预案。

**参考**：<https://swcregistry.io/docs/SWC-106>

---

## SS-107 Missing Access Control

**检测逻辑**：函数名为敏感管理名（`set*`、`mint`、`burn`、`pause`、`upgrade*`、
`transferOwnership`、`destroy`、`kill`、`sweep`、`rescue`、`initialize` 等），
可见性为 `public`/`external`，函数会写状态或产生外部调用/自毁/委托调用，
且函数头或函数体中没有 `onlyOwner`、`onlyRole`、`msg.sender ==` 等权限信号。

**为什么危险**：任意地址可调用管理函数，直接接管合约或转走资金。

**误报边界**：

- `withdraw` 等面向用户的函数不在敏感名列表中，避免把正常提款误判为管理入口；
- 使用自定义权限库（如 `AccessControl` 的 `onlyRole`）会被识别；
- 权限校验在修饰符内部、但未出现在函数头/函数体时，可能误报 → 建议使用标准修饰符。

**修复**：添加 `onlyOwner`/`onlyRole` 或显式 `require(msg.sender == owner)`；
补充未授权调用的负向测试。

**参考**：<https://swcregistry.io/docs/SWC-105>

---

## 局限

SolSentry_28 是模式匹配工具，不是编译器或符号执行引擎。以下情况可能漏报或误报：

- 跨函数、跨合约、跨交易的状态依赖；
- 继承、库调用、内联汇编与复杂控制流；
- 动态数组/结构体字段的别名与间接写入；
- 业务逻辑漏洞、经济模型漏洞、治理攻击。

因此，报告中的每条结果都应被视为**待复核线索**，而不是最终结论。
