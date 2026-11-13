import hashlib
import json
import os
import threading

from web3 import Web3
from web3.logs import DISCARD
from web3.middleware import ExtraDataToPOAMiddleware

# Connect to the blockchain with our account
w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
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
    global next_nonce
    chain_nonce = w3.eth.get_transaction_count(account.address, "pending")
    nonce = max(chain_nonce, next_nonce)  # never go backwards

    tx = function_call.build_transaction({"from": account.address, "nonce": nonce})
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    next_nonce = nonce + 1
    return w3.eth.wait_for_transaction_receipt(tx_hash)

def hash_record(audit_json):
    # SHA-256 fingerprint of the audit record text
    return hashlib.sha256(audit_json.encode()).digest()


def approve_loan(audit_json):
    # Fingerprint the decision records (memo, valuation, underwriter, terms)
    loan = json.loads(audit_json)
    audit_hash = hash_record(audit_json)
    # Anonymise the borrower: only a salted hash goes on the public chain
    salt = os.environ["BORROWER_ID_SALT"]
    borrower_id = hashlib.sha256((salt + loan["borrowerId"]).encode()).digest()

    with lock:
        # Mint the loan note NFT with the loan's terms
        mint = send(
            loan_note.functions.issue(
                account.address,
                round(loan["principal"] * 100),   # euros -> cents
                round(loan["aprPercent"] * 100),  # 4.5% -> 450 basis points
                loan["termMonths"],
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

def verify(token_id, audit_json):
    # Re-hash the saved record and compare it with the hash stored on chain
    on_chain = registry.functions.hashes(token_id).call()
    recomputed = hash_record(audit_json)
    return {
        "tokenId": token_id,
        "onChainHash": "0x" + bytes(on_chain).hex(),
        "recordHash": "0x" + recomputed.hex(),
        "match": bytes(on_chain) == recomputed,
    }