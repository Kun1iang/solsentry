// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MultilineCall {
    function pay(address payable to, uint256 amount) external {
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "transfer failed");
    }
}
