import hashlib
import json
import os
import threading

from web3 import Web3
from web3.logs import DISCARD

# Connect to the blockchain with our account
w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
account = w3.eth.account.from_key(os.environ["PRIVATE_KEY"])

# Load our two deployed contracts: their address, and their ABI (list of functions)
loan_note = w3.eth.contract(
    address=os.environ["LOAN_NOTE_ADDRESS"], abi=json.load(open("abi/LoanNote.json"))
)
registry = w3.eth.contract(
    address=os.environ["REGISTRY_ADDRESS"], abi=json.load(open("abi/HashRegistry.json"))
)

# Only one approval writes to the chain at a time
lock = threading.Lock()


def send(function_call):
    # Sign a transaction with our key, send it, and wait until it's in a block.
    tx = function_call.build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def approve_loan(app_id, loan):
    # Fingerprint the decision records (memo, valuation, underwriter, terms)
    audit_record = {"applicationId": app_id, **loan.model_dump()}
    audit_hash = hashlib.sha256(json.dumps(audit_record, sort_keys=True).encode()).digest()

    # Anonymise the borrower: only a salted hash goes on the public chain
    salt = os.environ["BORROWER_ID_SALT"]
    borrower_id = hashlib.sha256((salt + loan.borrowerId).encode()).digest()

    with lock:
        # Mint the loan note NFT with the loan's terms
        mint = send(
            loan_note.functions.issue(
                account.address,
                round(loan.principal * 100),   # euros -> cents
                round(loan.aprPercent * 100),  # 4.5% -> 450 basis points
                loan.termMonths,
                borrower_id,
            )
        )
        token_id = loan_note.events.LoanIssued().process_receipt(mint, errors=DISCARD)[0].args.loanId

        # Store the audit hash under the same loan number
        audit = send(registry.functions.commit(token_id, audit_hash))

    return {
        "tokenId": token_id,
        "auditHash": "0x" + audit_hash.hex(),
        "txHash": "0x" + mint.transactionHash.hex(),
        "auditTxHash": "0x" + audit.transactionHash.hex(),
    }