from typing import Literal, Optional

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import chain
from models import (
    AffordabilityIn,
    ApplicationForm,
    PropertySpec,
    Status,
    StressTestCreate, ApprovalIn,
)

app = FastAPI(title="AL Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://alagenticlender.onrender.com"],  # TODO add deployed web app url
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- applications ----------

@app.post("/applications", status_code=201)
def create_application(body: ApplicationForm, authorization: Optional[str] = Header(None)):
    # TODO: take borrowerId from the verified login token, save to Firestore
    return {"id": "app_1", "status": "Submitted"}

@app.post("/valuation")
def valuation(body: PropertySpec, authorization: Optional[str] = Header(None)):
    return {"estimatedPrice": 350000}


@app.post("/applications/{app_id}/approve")
def approve(app_id: str, body: ApprovalIn, authorization: Optional[str] = Header(None)):
    # TODO: check role, check status, save to Firestore
    try:
        result = chain.approve_loan(app_id, body)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Blockchain error: {error}")
    return {"id": app_id, "status": "Underwriter Approved", **result}

# ---------- calculators / models ----------
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
def create_payment_intent():
    raise HTTPException(status_code=501, detail="Not implemented in Sprint 1")


@app.post("/payments/webhook")
def payments_webhook():
    raise HTTPException(status_code=501, detail="Not implemented in Sprint 1")