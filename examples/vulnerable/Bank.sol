// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title VulnerableBank
/// @notice Deliberately insecure contract used by SolSentry's regression suite.
contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "insufficient balance");
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
        balances[msg.sender] -= amount;
    }

    function setOwner(address newOwner) external {
        require(tx.origin == owner, "not owner");
        owner = newOwner;
    }

    function sweep(address payable to) external {
        (bool sent, ) = to.call{value: address(this).balance}("");
        sent;
    }
}
