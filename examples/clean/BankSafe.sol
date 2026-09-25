// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title SafeBank
/// @notice Reference implementation: checks-effects-interactions + reentrancy guard.
contract SafeBank {
    mapping(address => uint256) public balances;
    address public owner;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "reentrant call");
        locked = true;
        _;
        locked = false;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external nonReentrant {
        require(balances[msg.sender] >= amount, "insufficient balance");
        balances[msg.sender] -= amount;
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "transfer failed");
    }

    function setOwner(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
