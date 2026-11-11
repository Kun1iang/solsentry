# SolSentry_28 扫描报告

> 目标：`examples/vulnerable`  
> 生成时间：2026-11-09T11:27:37+08:00  
> 工具版本：SolSentry_28 v1.0.0

## 概览

| 指标 | 值 |
| --- | --- |
| 文件 / 行数 | 3 / 101 |
| 问题总数 | 11 |
| 风险分 | 84/100（F，严重风险） |
| 抑制 / 错误 | 0 / 0 |

## 风险分布

| 等级 | 数量 |
| --- | ---: |
| 严重 | 0 |
| 高危 | 5 |
| 中危 | 6 |
| 低危 | 0 |
| 提示 | 0 |

## 发现

### 1. [高危] SS-101 Reentrancy

- 位置：`examples/vulnerable/Bank.sol:20:33`
- 函数：`withdraw`
- 置信度：medium
- 参考：SWC-107 / CWE-841
- 证据：`(bool ok, ) = msg.sender.call{value: amount}("");`

函数 withdraw 在外部调用后仍更新状态变量 balances，存在重入窗口。

**修复建议：** 遵循 Checks-Effects-Interactions：先更新状态，再进行外部调用；或使用 OpenZeppelin ReentrancyGuard 的 nonReentrant 修饰符，并补充重入测试。

### 2. [高危] SS-102 tx.origin Authentication

- 位置：`examples/vulnerable/Bank.sol:26:17`
- 函数：`setOwner`
- 置信度：high
- 参考：SWC-115 / CWE-284
- 证据：`require(tx.origin == owner, "not owner");`

函数 setOwner 使用 tx.origin 做身份判断；钓鱼合约可诱导受害者触发调用并继承其权限。

**修复建议：** 改用 msg.sender 校验身份；若需要兼容元交易，使用 EIP-2771 可信转发器并校验转发器地址与 calldata。

### 3. [高危] SS-102 tx.origin Authentication

- 位置：`examples/vulnerable/Lottery.sol:32:17`
- 函数：`withdrawPot`
- 置信度：high
- 参考：SWC-115 / CWE-284
- 证据：`require(tx.origin == owner, "not owner");`

函数 withdrawPot 使用 tx.origin 做身份判断；钓鱼合约可诱导受害者触发调用并继承其权限。

**修复建议：** 改用 msg.sender 校验身份；若需要兼容元交易，使用 EIP-2771 可信转发器并校验转发器地址与 calldata。

### 4. [高危] SS-104 Delegatecall to Dynamic Target

- 位置：`examples/vulnerable/Proxy.sol:24:48`
- 函数：`execute`
- 置信度：high
- 参考：SWC-112 / CWE-829
- 证据：`(bool ok, bytes memory result) = target.delegatecall(data);`

函数 execute 对动态目标执行 delegatecall，攻击者可能控制执行逻辑并改写当前合约存储。

**修复建议：** 将实现地址限制为不可变常量或受权限控制的 EIP-1967 槽位；升级入口必须加onlyOwner/onlyRole，并对目标代码哈希做白名单校验。

### 5. [高危] SS-106 Selfdestruct Usage

- 位置：`examples/vulnerable/Proxy.sol:30:9`
- 函数：`destroy`
- 置信度：high
- 参考：SWC-106 / CWE-284
- 证据：`selfdestruct(payable(msg.sender));`

函数 destroy 调用 selfdestruct，可能强制转移余额并删除合约代码，破坏既有安全假设。

**修复建议：** 移除 selfdestruct，改用 pause + withdraw 的受控下架流程；若必须保留，添加强权限控制、事件记录与迁移预案。

### 6. [中危] SS-107 Missing Access Control

- 位置：`examples/vulnerable/Bank.sol:25:5`
- 函数：`setOwner`
- 置信度：low
- 参考：SWC-105 / CWE-284
- 证据：`function setOwner(address newOwner) external {`

敏感函数 setOwner 为 public/external 且未见权限校验，任意地址均可调用并修改关键状态。

**修复建议：** 添加 onlyOwner/onlyRole 修饰符或 require(msg.sender == owner)，并为未授权调用补充负向测试。

### 7. [中危] SS-107 Missing Access Control

- 位置：`examples/vulnerable/Bank.sol:30:5`
- 函数：`sweep`
- 置信度：low
- 参考：SWC-105 / CWE-284
- 证据：`function sweep(address payable to) external {`

敏感函数 sweep 为 public/external 且未见权限校验，任意地址均可调用并修改关键状态。

**修复建议：** 添加 onlyOwner/onlyRole 修饰符或 require(msg.sender == owner)，并为未授权调用补充负向测试。

### 8. [中危] SS-103 Unchecked Low-Level Call

- 位置：`examples/vulnerable/Bank.sol:31:27`
- 函数：`sweep`
- 置信度：medium
- 参考：SWC-104 / CWE-252
- 证据：`(bool sent, ) = to.call{value: address(this).balance}("");`

函数 sweep 的 .call 返回值未被检查，调用失败时交易仍会继续执行。

**修复建议：** 捕获返回值并使用 require(success, "call failed") 或 if (!success) revert 检查；优先使用经过审计的转账库。

### 9. [中危] SS-105 Weak On-Chain Randomness

- 位置：`examples/vulnerable/Lottery.sol:23:1`
- 函数：`draw`
- 置信度：medium
- 参考：SWC-120 / CWE-330
- 证据：`keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))`

函数 draw 使用区块变量生成随机结果，验证者可预测或影响抽取过程。

**修复建议：** 使用 Chainlink VRF 等可验证随机函数；若只用于非资金场景，应在文档中明确其可预测性并限制经济影响。

### 10. [中危] SS-107 Missing Access Control

- 位置：`examples/vulnerable/Proxy.sol:15:5`
- 函数：`upgradeTo`
- 置信度：low
- 参考：SWC-105 / CWE-284
- 证据：`function upgradeTo(address newImplementation) external {`

敏感函数 upgradeTo 为 public/external 且未见权限校验，任意地址均可调用并修改关键状态。

**修复建议：** 添加 onlyOwner/onlyRole 修饰符或 require(msg.sender == owner)，并为未授权调用补充负向测试。

### 11. [中危] SS-107 Missing Access Control

- 位置：`examples/vulnerable/Proxy.sol:29:5`
- 函数：`destroy`
- 置信度：low
- 参考：SWC-105 / CWE-284
- 证据：`function destroy() external {`

敏感函数 destroy 为 public/external 且未见权限校验，任意地址均可调用并修改关键状态。

**修复建议：** 添加 onlyOwner/onlyRole 修饰符或 require(msg.sender == owner)，并为未授权调用补充负向测试。
