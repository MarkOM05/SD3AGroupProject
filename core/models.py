from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

BER = Literal["A1","A2","A3","B1","B2","B3","C1","C2","C3","D1","D2","E1","E2","F","G"]
Role = Literal["borrower", "broker", "underwriter"]
Decision = Literal["Approve", "Conditionally Approve", "Decline"]

class Status(str, Enum):
    applied = "Applied"
    ai_deliberated = "AI Deliberated"
    approved = "Underwriter Approved"
    funded = "Funded"
    closed = "Closed"
    declined = "Declined"

# ---------- what clients SEND ----------
class PropertySpec(BaseModel):          # used by /valuation
    county: str
    sizeSqm: int = Field(gt=0)
    bedrooms: int = Field(ge=0)
    type: str
    berRating: BER

class Property(PropertySpec):
    askingPrice: int = Field(gt=0)

class ApplicationCreate(BaseModel):     # borrowerId comes from the login token
    loanType: Literal["Mortgage", "HELOC"]
    income: int = Field(gt=0)
    debts: int = Field(ge=0)
    deposit: int = Field(ge=0)
    termYears: int = Field(ge=1, le=40)
    property: Property

class AffordabilityIn(BaseModel):
    income: int = Field(gt=0)
    debts: int = Field(ge=0)
    deposit: int = Field(ge=0)
    termYears: int = Field(ge=1, le=40)

class StressTestCreate(BaseModel):
    rateShockBps: int = Field(ge=100, le=300)

# ---------- what is STORED / returned ----------
class Application(ApplicationCreate):
    borrowerId: str
    brokerId: str | None = None
    status: Status = Status.applied
    mlValuation: int | None = None
    ltv: float | None = None              # percent, e.g. 82.5
    ltvBand: str | None = None
    dti: float | None = None              # percent, e.g. 34.0
    approvalLikelihood: float | None = None   # percent, 0-100
    riskTier: str | None = None
    decision: Decision | None = None
    aprBps: int | None = None             # 425 = 4.25%
    creditMemo: str | None = None
    auditHash: str | None = None
    tokenId: int | None = None
    txHash: str | None = None
    createdAt: datetime
    updatedAt: datetime | None = None

class User(BaseModel):
    name: str
    role: Role
    email: EmailStr
    assignedBrokerId: str | None = None
    createdAt: datetime

class AgentLog(BaseModel):
    agentName: str
    modelUsed: str
    reasoning: str
    output: dict | None = None
    confidence: float = Field(ge=0, le=100)
    timestamp: datetime

class Document(BaseModel):
    fileName: str
    fileType: str
    storagePath: str
    uploadedBy: str
    uploadedAt: datetime

class Message(BaseModel):
    senderId: str
    senderRole: Role
    text: str
    timestamp: datetime
    read: bool = False

class Payment(BaseModel):
    applicationId: str
    userId: str
    amount: int                           # cents
    currency: str
    purpose: Literal["fast_track_appraisal", "verification_fee"]
    provider: Literal["stripe", "paypal"]
    status: Literal["pending", "succeeded", "failed"]
    createdAt: datetime

class Review(BaseModel):
    userId: str
    rating: int = Field(ge=1, le=5)
    comment: str
    createdAt: datetime

class SupportTicket(BaseModel):
    userId: str
    subject: str
    message: str
    status: Literal["open", "closed"] = "open"
    createdAt: datetime

class StressTest(StressTestCreate):
    createdBy: str
    portfolioSnapshot: dict
    results: dict
    createdAt: datetime