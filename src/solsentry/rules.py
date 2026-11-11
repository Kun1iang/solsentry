"""Rule metadata for SolSentry_28.

Every rule carries a stable identifier, a severity, and a mapping to the
Smart Contract Weakness Classification (SWC) registry and MITRE CWE.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    """A single static-analysis rule."""

    id: str
    title: str
    severity: str
    swc: str
    cwe: str
    description: str
    remediation: str
    confidence: str = "medium"


RULES: tuple[Rule, ...] = (
    Rule(
        id="SS-101",
        title="Reentrancy",
        severity="high",
        swc="SWC-107",
        cwe="CWE-841",
        description=(
            "函数在外部调用之后仍写入合约状态，攻击者可在状态更新前重入该函数，"
            "重复提取资金或破坏账本一致性。"
        ),
        remediation=(
            "遵循 Checks-Effects-Interactions：先更新状态，再进行外部调用；"
            "或使用 OpenZeppelin ReentrancyGuard 的 nonReentrant 修饰符，并补充重入测试。"
        ),
    ),
    Rule(
        id="SS-102",
        title="tx.origin Authentication",
        severity="high",
        swc="SWC-115",
        cwe="CWE-284",
        description=(
            "使用 tx.origin 进行身份校验会绕过中间合约的意图，钓鱼合约可诱导受害者"
            "触发调用并继承其权限。"
        ),
        remediation=(
            "改用 msg.sender 校验身份；若需要兼容元交易，使用 EIP-2771 可信转发器并校验"
            "转发器地址与 calldata。"
        ),
    ),
    Rule(
        id="SS-103",
        title="Unchecked Low-Level Call",
        severity="medium",
        swc="SWC-104",
        cwe="CWE-252",
        description=(
            "低级调用 call/send 返回的布尔值未被检查，调用失败时交易仍会继续执行，"
            "可能造成状态与资金不一致。"
        ),
        remediation=(
            "捕获返回值并使用 require(success, \"call failed\") 或 if (!success) revert 检查；"
            "优先使用经过审计的转账库。"
        ),
    ),
    Rule(
        id="SS-104",
        title="Delegatecall to Dynamic Target",
        severity="high",
        swc="SWC-112",
        cwe="CWE-829",
        description=(
            "delegatecall 的目标来自参数或可变状态，攻击者可控制执行逻辑并在当前合约"
            "上下文中改写存储。"
        ),
        remediation=(
            "将实现地址限制为不可变常量或受权限控制的 EIP-1967 槽位；升级入口必须加"
            "onlyOwner/onlyRole，并对目标代码哈希做白名单校验。"
        ),
    ),
    Rule(
        id="SS-105",
        title="Weak On-Chain Randomness",
        severity="medium",
        swc="SWC-120",
        cwe="CWE-330",
        description=(
            "使用 block.timestamp、blockhash 等链上可观测值生成随机数，验证者或"
            "套利者可预测甚至影响结果。"
        ),
        remediation=(
            "使用 Chainlink VRF 等可验证随机函数；若只用于非资金场景，应在文档中明确"
            "其可预测性并限制经济影响。"
        ),
    ),
    Rule(
        id="SS-106",
        title="Selfdestruct Usage",
        severity="high",
        swc="SWC-106",
        cwe="CWE-284",
        description=(
            "selfdestruct 会强制转移余额并删除代码，且在上海升级后语义发生变化，"
            "可能破坏代理、审计与资金安全假设。"
        ),
        remediation=(
            "移除 selfdestruct，改用 pause + withdraw 的受控下架流程；若必须保留，"
            "添加强权限控制、事件记录与迁移预案。"
        ),
    ),
    Rule(
        id="SS-107",
        title="Missing Access Control",
        severity="medium",
        swc="SWC-105",
        cwe="CWE-284",
        description=(
            "敏感管理函数为 public/external 且未见权限校验，任意地址均可调用并修改"
            "关键状态。"
        ),
        remediation=(
            "添加 onlyOwner/onlyRole 修饰符或 require(msg.sender == owner)，并为未授权"
            "调用补充负向测试。"
        ),
    ),
)

RULES_BY_ID: dict[str, Rule] = {rule.id: rule for rule in RULES}

SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

SEVERITY_LABELS: dict[str, str] = {
    "critical": "严重",
    "high": "高危",
    "medium": "中危",
    "low": "低危",
    "info": "提示",
}

SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 30,
    "high": 12,
    "medium": 4,
    "low": 1,
    "info": 0,
}
