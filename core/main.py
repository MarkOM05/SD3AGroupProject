from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from typing import Literal

app = FastAPI()

class Property(BaseModel):
    county: str
    sizeSqm: int
    bedrooms: int
    type: str
    berRating: Literal["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "E1", "E2", "F", "G"]
    askingPrice: int

class User(BaseModel):
    name: str
    role: str
    email: EmailStr
    assignedBrokerId: str | None = None
    createdAt: str

class Application(BaseModel):
    borrowerId: str
    brokerId: str | None
    loanType: str
    income: int
    debts: int
    deposit: int
    termYears: int
    property: Property
    status: str
    mlValuation: int
    ltv: int
    ltvBand: str
    dti: int
    approvalLikelihood: int
    riskTier: str
    decision: str | None
    apr: int | None
    creditMemo: str | None
    auditHash: str | None
    # TODO blockchain
    createdAt: str
    updatedAt: str | None

class AgentLog(BaseModel):
    agentName: str
    modelUsed: str
    reasoning :str
    # TODO output
    confidence: int
    timestamp: str

class Document(BaseModel):
    fileName: str
    fileType: str
    storagePath: str
    uploadedBy: str # userId
    uploadedAt: str

class Message(BaseModel):
    senderId: str
    senderRole: str
    text: str
    timestamp: str
    read: bool

class Payment(BaseModel):
    applicationId: str
    userId: str
    amount: float
    currency: str
    purpose: str
    provider: str
    status: str
    createdAt: str

class Review(BaseModel):
    userId: str
    rating: str
    comment: str
    createdAt: str

class SupportTicket(BaseModel):
    userId: str
    subject: str
    message: str
    status: str
    createdAt: str

class StressTest(BaseModel):
    createdBy: str
    rateShockBps: str
    portfolioSnapshot: str
    results: str
    createdAt: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/applications")
def applications():
    print()
    # TODO

@app.post("/applications")
def applications():
    print()
    # TODO

@app.post("/applications/{id}/deliberate")
def deliberate(appId: str):
    print(appId)
    # TODO

@app.post("/applications/{id}/approve")
def approve(appId: str):
    print()
    # TODO

@app.get("/applications/{id}/audit-pack")
def audit_pack(appId: str):
    print()
    # TODO

@app.post("/valuation")
def valuation():
    print()
    # TODO

@app.post("/stress-test")
def stress_test():
    print()
    # TODO

@app.post("/payments")
def payments():
    print()
    # TODO
