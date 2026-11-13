// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract HashRegistry {
    mapping(uint256 => bytes32) public hashes;

    event HashCommitted(uint256 indexed recordId, bytes32 fileHash, address committedBy);

    function commit(uint256 recordId, bytes32 fileHash) external {
        require(fileHash != bytes32(0), "empty hash");
        require(hashes[recordId] == bytes32(0), "already committed");
        hashes[recordId] = fileHash;
        emit HashCommitted(recordId, fileHash, msg.sender);
    }
}