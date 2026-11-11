// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title SimpleToken
/// @notice Clean baseline used to check that SolSentry_28 stays quiet on common code.
contract SimpleToken {
    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor(uint256 supply) {
        owner = msg.sender;
        totalSupply = supply;
        balanceOf[msg.sender] = supply;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        totalSupply += amount;
        balanceOf[to] += amount;
    }
}
