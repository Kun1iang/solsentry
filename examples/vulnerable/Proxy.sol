// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title UnsafeProxy
/// @notice Dynamic delegatecall, unguarded upgrade path, and selfdestruct demo.
contract UnsafeProxy {
    address public implementation;
    address public owner;

    constructor(address firstImplementation) {
        implementation = firstImplementation;
        owner = msg.sender;
    }

    function upgradeTo(address newImplementation) external {
        implementation = newImplementation;
    }

    function execute(address target, bytes calldata data)
        external
        payable
        returns (bytes memory)
    {
        (bool ok, bytes memory result) = target.delegatecall(data);
        require(ok, "delegatecall failed");
        return result;
    }

    function destroy() external {
        selfdestruct(payable(msg.sender));
    }
}
