import json
import os
from typing import Literal, Optional

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware

import chain
import store
from store import SERVER_TIMESTAMP, db, require_role
from affordibility import check_affordability

import stripe

from models import (
    AffordabilityIn,
    ApplicationForm,
    PropertySpec,
    Status,
    StressTestCreate,
    ApprovalIn,
    CheckoutRequest
)

stripe.api_key = os.environ["STRIPE_PRIVATE_KEY"]

app = FastAPI(title="AL Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://alagenticlender.onrender.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payment prices
PRICES = {
    "fast_track_appraisal": 4900,
}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- applications ----------

@app.post("/applications", status_code=201)
def create_application(form: ApplicationForm, authorization: Optional[str] = Header(None)):
    borrower_id = require_role(authorization, "borrower")
    _, ref = db.collection("applications").add({
        **form.model_dump(),
        "borrowerId": borrower_id,
        "status": "submitted",
        "createdAt": SERVER_TIMESTAMP,
    })
    return {"applicationId": ref.id}

@app.post("/valuation")
def valuation(body: PropertySpec, authorization: Optional[str] = Header(None)):
    return {"estimatedPrice": 350000}


APPROVABLE = {"Applied", Status.submitted.value, Status.ai_deliberated.value}

@app.post("/applications/{app_id}/approve")
def approve(app_id: str, body: ApprovalIn, authorization: Optional[str] = Header(None)):
    # 1. Only a logged-in underwriter may approve
    underwriter_id = store.require_role(authorization, "underwriter")

    # 2. Load the application and mark it "Approving" in one step,
    #    so a double-click can't mint two loan notes
    ref = store.db.collection("applications").document(app_id)
    application = store.claim(store.db.transaction(), ref, APPROVABLE, Status.approving.value)

    # 3. The audit record: everything this decision was based on
    audit_record = {
        "applicationId": app_id,
        "borrowerId": application["borrowerId"],
        "underwriterId": underwriter_id,
        "loanType": application["loanType"],
        "income": application["income"],
        "debts": application["debts"],
        "deposit": application["deposit"],
        "property": application["property"],
        "valuation": application.get("mlValuation"),
        "principal": application["property"]["askingPrice"] - application["deposit"],
        "termMonths": application["termYears"] * 12,
        "aprPercent": body.aprPercent,
        "creditMemo": body.creditMemo,
    }
    audit_json = json.dumps(audit_record, sort_keys=True)

    # 4. Write to the blockchain
    try:
        result = chain.approve_loan(audit_json)
    except Exception as error:
        ref.update({"status": application["status"]})  # put the old status back
        raise HTTPException(status_code=502, detail=f"Blockchain error: {error}")

    # 5. Save the results, including the exact text we hashed (needed to verify later)
    ref.update({
        "status": Status.approved.value,
        "aprBps": round(body.aprPercent * 100),
        "creditMemo": body.creditMemo,
        "auditRecord": audit_json,
        "approvedBy": underwriter_id,
        "updatedAt": store.SERVER_TIMESTAMP,
        **result,  # tokenId, auditHash, txHash, auditTxHash
    })
    return {"id": app_id, "status": Status.approved.value, **result}


@app.get("/applications/{app_id}/verify")
def verify(app_id: str):
    # Anyone can check that the saved audit record still matches the chain
    snapshot = store.db.collection("applications").document(app_id).get()
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Application not found")
    application = snapshot.to_dict()
    if "auditRecord" not in application:
        raise HTTPException(status_code=409, detail="This application has no on-chain record yet")
    try:
        result = chain.verify(application["tokenId"], application["auditRecord"])
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Blockchain error: {error}")
    return {"id": app_id, **result}


# ---------- calculators / models ----------

@app.post("/affordability-estimate")
def affordability_estimate(body: AffordabilityIn):
    return check_affordability(**body.model_dump())
@app.post("/affordability")
def affordability(body: AffordabilityIn, authorization: Optional[str] = Header(None)):
    # TODO: run the LangGraph affordability agent
    return {
        "affordable": True,
        "figures": {
            "netMonthlyIncome": 5200,
            "repaymentBase": 1530,
            "repaymentStressed": 1890,
            "surplus": 2410,
            "loanToIncome": 3.8,
        },
        "reasons": ["Loan is within the borrowing cap", "Surplus is positive at the stressed rate"],
        "toolTrace": [{"tool": "calc_repayment", "input": {"rate": 4.0}, "output": {"monthly": 1530}}],
    }

# ---------- Later sprints (not implemented yet) ----------

@app.post("/applications/{app_id}/deliberate", status_code=202)
def deliberate(app_id: str, background: BackgroundTasks):
    # TODO: background.add_task(run_committee, app_id)
    return {"id": app_id, "job": "started"}

@app.post("/applications/{app_id}/decline")
def decline(app_id: str):
    raise HTTPException(status_code=501, detail="Not implemented in Sprint 1")


@app.get("/applications/{app_id}/audit-pack")
def audit_pack(app_id: str, format: Literal["pdf", "csv"] = "pdf"):
    raise HTTPException(status_code=501, detail="Not implemented in Sprint 1")


@app.post("/stress-test")
def stress_test(body: StressTestCreate):
    raise HTTPException(status_code=501, detail="Not implemented in Sprint 1")


@app.post("/payments/create-intent")
def create_payment_intent(body: CheckoutRequest, authorization: Optional[str] = Header(None)):
    uid = require_role(authorization, "applicant")  # use whichever role pays

    amount = PRICES.get(body.purpose)
    if amount is None:
        raise HTTPException(400, "Unknown purpose")

    app_doc = db.collection("applications").document(body.applicationId).get()
    if not app_doc.exists or app_doc.get("userId") != uid:
        raise HTTPException(403, "Not your application")

    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency="eur",
        automatic_payment_methods={"enabled": True},
        metadata={
            "userId": uid,
            "applicationId": body.applicationId,
            "purpose": body.purpose,
        },
    )

    db.collection("payments").document(intent.id).set({
        "amount": amount,
        "currency": "eur",
        "provider": "stripe",
        "purpose": body.purpose,
        "applicationId": body.applicationId,
        "userId": uid,
        "status": "pending",
        "stripePaymentIntentId": intent.id,
        "createdAt": store.SERVER_TIMESTAMP,
    })

    return {"clientSecret": intent.client_secret}

def update_payment(intent: dict, status: str):
    ref = db.collection("payments").document(intent["id"])
    ref.set({
        "status": status,
        "updatedAt": store.SERVER_TIMESTAMP,
    }, merge=True)

    if status == "succeeded" and intent["metadata"].get("purpose") == "fast_track_appraisal":
        db.collection("applications").document(intent["metadata"]["applicationId"]).set(
            {"fastTrack": True}, merge=True
        )

@app.post("/payments/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, request.headers.get("stripe-signature"), os.environ["WEBHOOK_SECRET"]
        )
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook")

    intent = event["data"]["object"]
    if event["type"] == "payment_intent.succeeded":
        await update_payment(intent, "succeeded")
    elif event["type"] == "payment_intent.payment_failed":
        await update_payment(intent, "failed")

    return {"received": True}