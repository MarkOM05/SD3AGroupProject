from typing import Literal, Optional

from fastapi import BackgroundTasks, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    AffordabilityIn,
    ApplicationCreate,
    PropertySpec,
    Status,
    StressTestCreate,
)

app = FastAPI(title="AL Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # TODO add deployed web app url
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- applications ----------
@app.get("/applications")
def list_applications(
    status: Optional[Status] = None,
    riskTier: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    # TODO: query Firestore (brokers see only their own clients)
    return [
        {
            "id": "app_1",
            "status": "Applied",
            "ltv": 82.5,
            "ltvBand": "80-90%",
            "dti": 34.0,
            "riskTier": "B",
        }
    ]


@app.post("/applications", status_code=201)
def create_application(body: ApplicationCreate):
    # TODO: take borrowerId from the verified login token, save to Firestore
    return {"id": "app_1", "status": "Applied"}


@app.get("/applications/{app_id}")
def get_application(app_id: str):
    return {
        "id": app_id,
        "borrowerId": "user_1",
        "brokerId": None,
        "loanType": "Mortgage",
        "status": "Applied",
        "mlValuation": 350000,
        "ltv": 82.5,
        "ltvBand": "80-90%",
        "dti": 34.0,
        "approvalLikelihood": 70.0,
        "riskTier": "B",
        "decision": None,
        "aprBps": None,
        "creditMemo": None,
        "auditHash": None,
        "tokenId": None,
        "txHash": None,
    }


@app.post("/applications/{app_id}/deliberate", status_code=202)
def deliberate(app_id: str, background: BackgroundTasks):
    # TODO: background.add_task(run_committee, app_id)
    return {"id": app_id, "job": "started"}


@app.get("/applications/{app_id}/deliberation")
def get_deliberation(app_id: str):
    return {
        "id": app_id,
        "decision": "Conditionally Approve",
        "agentLogs": [
            {
                "agentName": "Affordability Agent",
                "modelUsed": "placeholder",
                "reasoning": "TODO",
                "output": None,
                "confidence": 75.0,
                "timestamp": "2026-01-01T12:00:00Z",
            }
        ],
    }


@app.post("/applications/{app_id}/approve")
def approve(app_id: str):
    # TODO: check role, check status, hash memo, mint on-chain, save to Firestore
    return {
        "id": app_id,
        "status": "Underwriter Approved",
        "auditHash": "0xFAKEHASH",
        "tokenId": 1,
        "txHash": "0xFAKE",
    }


@app.post("/applications/{app_id}/decline")
def decline(app_id: str):
    return {"id": app_id, "status": "Declined"}


@app.get("/applications/{app_id}/audit-pack")
def audit_pack(app_id: str, format: Literal["pdf", "csv"] = "pdf"):
    return {"id": app_id, "format": format, "url": "TODO"}


# ---------- calculators / models ----------
@app.post("/affordability")
def affordability(body: AffordabilityIn):
    return {"maxBorrowing": 400000, "dti": 34.0, "approvalLikelihood": 70.0}


@app.post("/valuation")
def valuation(body: PropertySpec):
    return {"estimatedPrice": 350000}


@app.post("/stress-test")
def stress_test(body: StressTestCreate):
    return {"rateShockBps": body.rateShockBps, "results": {}}


# ---------- payments ----------
@app.post("/payments/create-intent")
def create_payment_intent():
    return {"clientSecret": "fake_secret"}


@app.post("/payments/webhook")
def payments_webhook():
    return {"received": True}