// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract LoanNote is ERC721, Ownable {
    struct Loan {
        uint256 principalCents;
        uint32 aprBasisPoints;
        uint32 termMonths;
        bytes32 borrowerId;
    }

    mapping(uint256 => Loan) public loans;
    uint256 public totalIssued;

    event LoanIssued(uint256 indexed loanId, address indexed holder, bytes32 borrowerId);

    constructor(address initialOwner) ERC721("Loan Note", "LOAN") Ownable(initialOwner) {}

    function issue(
        address holder,
        uint256 principalCents,
        uint32 aprBasisPoints,
        uint32 termMonths,
        bytes32 borrowerId
    ) external onlyOwner returns (uint256 loanId) {
        require(principalCents > 0, "principal must be positive");
        require(termMonths > 0, "term must be positive");
        require(borrowerId != bytes32(0), "missing borrower ID");

        loanId = ++totalIssued;
        loans[loanId] = Loan(principalCents, aprBasisPoints, termMonths, borrowerId);
        _safeMint(holder, loanId);
        emit LoanIssued(loanId, holder, borrowerId);
    }
}