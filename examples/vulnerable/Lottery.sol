// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title WeakLottery
/// @notice Predictable randomness and tx.origin authentication demo.
contract WeakLottery {
    address public owner;
    mapping(address => uint256) public tickets;
    uint256 public pot;

    constructor() {
        owner = msg.sender;
    }

    function buy() external payable {
        require(msg.value == 1 ether, "ticket price");
        tickets[msg.sender] += 1;
        pot += msg.value;
    }

    function draw() external {
        uint256 random = uint256(
            keccak256(abi.encodePacked(block.timestamp, block.prevrandao, msg.sender))
        ) % 10;
        if (random == 0) {
            payable(msg.sender).transfer(pot);
            pot = 0;
        }
    }

    function withdrawPot() external {
        require(tx.origin == owner, "not owner");
        payable(msg.sender).transfer(address(this).balance);
    }
}
