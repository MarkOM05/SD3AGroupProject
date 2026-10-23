"""
seed.py - Seed AL (Agentic Lender) test data into Firebase Auth + Firestore.

Usage:
    pip install firebase-admin
    # put serviceAccountKey.json next to this file (NEVER commit it)
    python seed.py

Safe to re-run: users are looked up by email and every document uses a fixed
ID, so a second run overwrites instead of duplicating.

The Admin SDK bypasses security rules, so this works with locked-down rules.
Field names must match schema.md. All values below are placeholders.
"""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import auth, credentials, firestore

KEY_PATH = "serviceAccountKey.json"
TEST_PASSWORD = "AlTest#2026"  # test accounts only

cred = credentials.Certificate(KEY_PATH)
project_id = cred.project_id
answer = input(
    f"This writes test data to Firebase project '{project_id}'.\n"
    "Type the project id to continue: "
).strip()
if answer != project_id:
    sys.exit("Aborted.")

firebase_admin.initialize_app(cred)
db = firestore.client()

NOW = datetime.now(timezone.utc)


def ago(days=0, hours=0):
    return NOW - timedelta(days=days, hours=hours)


# ---------------------------------------------------------------------------
# 1. Auth users + custom role claims + users/{uid} documents
# ---------------------------------------------------------------------------
def ensure_user(email, name, role):
    """Create the Auth account if missing, then (re)set the role claim."""
    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        user = auth.create_user(email=email, password=TEST_PASSWORD, display_name=name)
    auth.set_custom_user_claims(user.uid, {"role": role})
    return user.uid


broker_uid = ensure_user("broker@al-test.com", "Test Broker", "broker")
other_broker_uid = ensure_user("broker2@al-test.com", "Other Broker", "broker")
underwriter_uid = ensure_user("underwriter@al-test.com", "Test Underwriter", "underwriter")
borrower_uid = ensure_user("borrower@al-test.com", "Test Borrower", "borrower")


def put_user(uid, role, name, email, **extra):
    db.collection("users").document(uid).set({
        "role": role,
        "displayName": name,
        "email": email,
        "assignedBrokerId": None,
        "createdAt": ago(30),
        **extra,
    })


put_user(broker_uid, "broker", "Test Broker", "broker@al-test.com")
put_user(other_broker_uid, "broker", "Other Broker", "broker2@al-test.com")  # for "wrong broker" rule tests
put_user(underwriter_uid, "underwriter", "Test Underwriter", "underwriter@al-test.com")
put_user(
    borrower_uid, "borrower", "Test Borrower", "borrower@al-test.com",
    assignedBrokerId=broker_uid,  # borrowers have no wallet; the bank owns the on-chain note
)

# ---------------------------------------------------------------------------
# 2. Applications at four lifecycle stages
# ---------------------------------------------------------------------------
def inputs(income, debts, deposit, term, county, sqm, beds, ptype, ber, asking):
    """Fields a borrower supplies (what the mobile app writes)."""
    return {
        "income": income,          # gross annual, EUR
        "debts": debts,            # monthly repayments on existing debts, EUR
        "deposit": deposit,        # EUR
        "termYears": term,
        "property": {
            "county": county, "sizeSqm": sqm, "bedrooms": beds,
            "type": ptype, "berRating": ber, "askingPrice": asking,
        },
    }


def valuation(inp, ml_value):
    """Fields the AI engine computes: mlValuation, ltv, ltvBand."""
    p = inp["property"]
    # Verified LTV uses the LOWER of asking price and ML valuation (see schema.md)
    ltv = round((p["askingPrice"] - inp["deposit"]) / min(p["askingPrice"], ml_value) * 100, 1)
    band = "<=60" if ltv <= 60 else "60-80" if ltv <= 80 else ">80"
    return {"mlValuation": ml_value, "ltv": ltv, "ltvBand": band}


def application(status, created, inp, **fields):
    return {
        "borrowerId": borrower_uid,
        "brokerId": broker_uid,
        "loanType": "mortgage",
        "status": status,
        **inp,
        "createdAt": created,
        "updatedAt": created,
        **fields,  # may override updatedAt
    }


def sha256_of(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


APP_APPLIED = "app_001_applied"
APP_DELIB = "app_002_deliberated"
APP_APPROVED = "app_003_approved"
APP_FUNDED = "app_004_funded"

# 1) Applied - exactly what a client may write: NO computed fields
inp1 = inputs(72000, 250, 40000, 30, "Cork", 95, 3, "semi-detached", "C1", 340000)
db.collection("applications").document(APP_APPLIED).set(
    application("Applied", ago(1), inp1)
)

# 2) AI Deliberated - AI engine has written valuation, risk and a recommendation
inp2 = inputs(85000, 400, 110000, 25, "Dublin", 78, 2, "apartment", "B3", 395000)
db.collection("applications").document(APP_DELIB).set(
    application(
        "AI Deliberated", ago(5), inp2, **valuation(inp2, 372000),
        dti=31.2, approvalLikelihood=0.78, riskTier="Medium",
        decision="Conditionally Approve", apr=4.35,
        creditMemo=(
            "Affordability is within limits. Asking price is 6.2% above the ML "
            "valuation, so verified LTV is based on the valuation. Approve "
            "conditional on a price renegotiation or larger deposit, and "
            "verification of the last three payslips."
        ),
        updatedAt=ago(4),
    )
)

# 3) Underwriter Approved - signed off; blockchain/auditHash not written yet
inp3 = inputs(98000, 0, 80000, 30, "Galway", 120, 4, "detached", "A3", 310000)
db.collection("applications").document(APP_APPROVED).set(
    application(
        "Underwriter Approved", ago(10), inp3, **valuation(inp3, 318000),
        dti=22.5, approvalLikelihood=0.91, riskTier="Low",
        decision="Approve", apr=3.90,
        creditMemo="Strong affordability and collateral fully supported by valuation.",
        updatedAt=ago(2),
    )
)

# 4) Funded - ledger has minted the loan note and stored the audit hash
inp4 = inputs(80000, 150, 55000, 30, "Limerick", 88, 3, "terraced", "B2", 275000)
memo4 = "Standard approval. LTV at 80%, collateral in line with valuation."
db.collection("applications").document(APP_FUNDED).set(
    application(
        "Funded", ago(20), inp4, **valuation(inp4, 280000),
        dti=27.8, approvalLikelihood=0.88, riskTier="Low",
        decision="Approve", apr=4.10, creditMemo=memo4,
        # Placeholder: agree the exact hashed payload with the ledger teammate
        auditHash=sha256_of({
            "creditMemo": memo4, "mlValuation": 280000,
            "decision": "Approve", "approvedBy": underwriter_uid,
        }),
        blockchain={
            "tokenId": 1,
            "txHash": "0x" + "ab" * 32,
            "contractAddress": "0x5FbDB2315678afecb367f032d93F642f64180aa3",  # Hardhat first deploy
            # Placeholder. The real value is keccak256(uid + appId), computed by the backend.
            # (hashlib has no keccak256, so sha256 stands in here.)
            "borrowerRef": "0x" + hashlib.sha256((borrower_uid + APP_FUNDED).encode()).hexdigest(),
        },
        updatedAt=ago(15),
    )
)

# ---------------------------------------------------------------------------
# 3. Subcollections
# ---------------------------------------------------------------------------
def sub(app_id, name, doc_id, data):
    db.collection("applications").document(app_id).collection(name).document(doc_id).set(data)


# agentLogs for the AI Deliberated application (all four agents)
agent_logs = [
    ("01_affordability", "Affordability", "groq:llama-3.3-70b",
     "Loan-to-income is 3.35x, within the 4x cap. Repayment stays affordable at +200 bps.",
     {"loanToIncome": 3.35, "stressedMonthlyRepayment": 1720,
      "netMonthlySurplus": 2150, "withinLtiCap": True}, 0.86),
    ("02_valuation", "Valuation", "gemini:gemini-2.0-flash",
     "Asking price is 6.2% above the ML estimate. Collateral flagged as overvalued.",
     {"mlValuation": 372000, "askingPrice": 395000, "overvaluedPct": 6.2,
      "verifiedLtv": 76.6, "flag": "overvalued"}, 0.81),
    ("03_market_macro", "MarketMacro", "ollama:llama3",
     "Rates are stable. Prevailing fixed mortgage rates sit around 4.2%.",
     {"centralBankRate": 2.0, "avgMortgageRate": 4.2, "trend": "stable"}, 0.70),
    ("04_underwriting_strategist", "UnderwritingStrategist", "ollama:mistral",
     "Upstream agents broadly agree. Recommend conditional approval pending price adjustment.",
     {"decision": "Conditionally Approve",
      "conditions": ["Renegotiate price toward valuation or increase deposit",
                     "Verify last 3 payslips"]}, 0.78),
]
for i, (log_id, agent, model, reasoning, output, conf) in enumerate(agent_logs):
    sub(APP_DELIB, "agentLogs", log_id, {
        "agentName": agent, "modelUsed": model, "reasoning": reasoning,
        "output": output, "confidence": conf,
        "timestamp": ago(5) + timedelta(minutes=i),
    })

# messages (borrower <-> broker) on the AI Deliberated application
messages = [
    ("m1", borrower_uid, "borrower", "Hi, is the price issue a problem for my application?", ago(4, 3), True),
    ("m2", broker_uid, "broker", "The valuation came in lower than the asking price. Let's discuss options.", ago(4, 2), True),
    ("m3", borrower_uid, "borrower", "Could a larger deposit fix it?", ago(4, 1), False),
]
for mid, sender, role, text, ts, read in messages:
    sub(APP_DELIB, "messages", mid, {
        "senderId": sender, "senderRole": role, "text": text,
        "timestamp": ts, "read": read,
    })

# document metadata (file itself would live in Firebase Storage)
sub(APP_APPLIED, "documents", "doc_payslip_1", {
    "fileName": "payslip_oct.pdf",
    "fileType": "application/pdf",
    "storagePath": f"documents/{APP_APPLIED}/payslip_oct.pdf",
    "uploadedBy": borrower_uid,
    "ocrExtractedData": {"grossMonthly": 6000, "deductions": 1450},
    "uploadedAt": ago(1),
})

# ---------------------------------------------------------------------------
# 4. Top-level collections
# ---------------------------------------------------------------------------
db.collection("payments").document("pay_001").set({
    "applicationId": APP_DELIB, "userId": borrower_uid,
    "amount": 4900, "currency": "eur",       # minor units (cents)
    "purpose": "appraisal_fast_track", "provider": "stripe",
    "status": "succeeded", "createdAt": ago(5),
})
db.collection("reviews").document("rev_001").set({
    "userId": borrower_uid, "rating": 5,
    "comment": "Clear and fast. Loved seeing the fair-price estimate.",
    "createdAt": ago(3),
})
db.collection("supportTickets").document("tkt_001").set({
    "userId": borrower_uid, "subject": "Payment receipt",
    "message": "Where can I download my appraisal fee receipt?",
    "status": "open", "createdAt": ago(2),
})
db.collection("stressTests").document("st_001").set({
    "createdBy": underwriter_uid, "rateShockBps": 200,
    "portfolioSnapshot": {"applications": 4, "totalExposure": 1010000},
    "results": {"atRiskApplications": 1, "avgDtiAfterShock": 36.4},
    "createdAt": ago(1),
})

# ---------------------------------------------------------------------------
print(f"\nSeeded project '{project_id}'. Test logins (password: {TEST_PASSWORD}):")
for label, email, uid in [
    ("borrower", "borrower@al-test.com", borrower_uid),
    ("broker", "broker@al-test.com", broker_uid),
    ("other broker", "broker2@al-test.com", other_broker_uid),
    ("underwriter", "underwriter@al-test.com", underwriter_uid),
]:
    print(f"  {label:<13} {email:<26} uid={uid}")
print("\nUsers must sign out and back in before their role claim takes effect.")
