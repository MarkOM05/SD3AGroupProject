# AL (Agentic Lender): Firestore Schema

**Owner:** AL-Core (team lead) | **Last updated:** `<date>` | **Version:** 0.1

This file is the contract between AL-Mobile, AL-Web, AL-AI Engine and the Ledger. If a field is not listed here, do not rely on it. To change the schema, open a pull request that edits this file **and** `firestore.rules` / `firestore.indexes.json`. Only the AL-Core owner deploys.

## 1. Project facts

| Item | Value |
|---|---|
| Firebase project ID | `<fill in>` |
| Firestore location | `europe-west1` (permanent) |
| Auth providers | Email/Password, Google |
| Storage bucket (files) | `<fill in>`; Firestore holds metadata only |

## 2. Conventions

- Field names are `camelCase`; collection names are plural `camelCase`.
- Dates and times are Firestore **Timestamp** values, never strings.
- Money is a **number in EUR** (whole euros) unless stated; payment `amount` is in **cents**.
- Percentages (`ltv`, `dti`, `apr`) are numbers like `76.6`, **not** `0.766`.
- `approvalLikelihood` is a number from `0` to `1`.
- `users/{uid}` uses the Firebase Auth UID as the document ID.
- Every `applications` write sets `updatedAt`.
- Use `null` for "not yet known"; do not use empty strings.

## 3. Roles

Roles are stored in Auth **custom claims** (`request.auth.token.role`) and mirrored in `users/{uid}.role`. Staff roles are assigned by the AL-Core owner only. Users must sign out and back in after a claim changes.

| Role | Access |
|---|---|
| `borrower` | Own profile and own applications; creates applications, messages, reviews, tickets |
| `broker` | Applications where `brokerId == own uid`, plus their messages, documents, agentLogs |
| `underwriter` | Read everything; sign off applications; stress tests |
| backend (Admin SDK) | Bypasses rules; writes computed, blockchain and payment data |

## 4. Application lifecycle

`Applied` → `AI Deliberated` → `Underwriter Approved` → `Funded` → `Closed`

| Transition | Set by | How |
|---|---|---|
| (create) → `Applied` | Mobile (or Web for broker-created files, if agreed) | Client write |
| `Applied` → `AI Deliberated` | AI Engine | Admin SDK, after writing valuation fields and agentLogs |
| `AI Deliberated` → `Underwriter Approved` | Web (underwriter) | Client write; rules enforce forward-only |
| `Underwriter Approved` → `Funded` | Ledger / backend | Admin SDK, after minting and writing `blockchain` + `auditHash` |
| `Funded` → `Closed` | Web (underwriter) | Client write |

## 5. Who writes what

| Data | Written by |
|---|---|
| Application inputs (`income`, `debts`, `deposit`, `termYears`, `property`) | Mobile / Web |
| `mlValuation`, `ltv`, `ltvBand`, `dti`, `approvalLikelihood`, `riskTier`, `apr`, `creditMemo`, initial `decision`, `agentLogs` | AI Engine |
| `decision` override, status → `Underwriter Approved` / `Closed` | Web (underwriter) |
| `blockchain`, `auditHash`, status → `Funded` | Ledger / backend |
| `payments` | Backend, after Stripe/PayPal confirms |
| `messages`, `reviews`, `supportTickets`, `documents` metadata | Clients |
| `stressTests` | Web (underwriter) |

**Fields a client may never supply on application create:** `mlValuation`, `ltv`, `ltvBand`, `dti`, `approvalLikelihood`, `riskTier`, `decision`, `apr`, `creditMemo`, `auditHash`, `blockchain`.

## 6. Collections

### `users/{uid}`

| Field | Type | Notes |
|---|---|---|
| `role` | string | `borrower` \| `broker` \| `underwriter` |
| `displayName` | string | |
| `email` | string | |
| `assignedBrokerId` | string \| null | Borrowers only; broker's uid. Set by staff, not by the user |
| `createdAt` | timestamp | |

### `applications/{appId}`

| Field | Type | Notes |
|---|---|---|
| `borrowerId` | string | Auth uid |
| `brokerId` | string | Auth uid of assigned broker |
| `loanType` | string | `mortgage` \| `heloc` |
| `income` | number | Gross annual household income |
| `debts` | number | Monthly repayments on existing debts *(see open decisions)* |
| `deposit` | number | |
| `termYears` | number | |
| `property` | map | See below |
| `status` | string | See lifecycle |
| `mlValuation` | number | AI Engine |
| `ltv` | number | Percent, AI Engine |
| `ltvBand` | string | `<=60` \| `60-80` \| `>80`; derived from `ltv` for indexed filtering |
| `dti` | number | Percent, AI Engine |
| `approvalLikelihood` | number | 0 to 1 |
| `riskTier` | string | `Low` \| `Medium` \| `High` |
| `decision` | string \| null | `Approve` \| `Conditionally Approve` \| `Decline` |
| `apr` | number \| null | Percent |
| `creditMemo` | string \| null | From the Underwriting Strategist agent |
| `auditHash` | string \| null | SHA-256 hex, written after on-chain sign-off |
| `blockchain` | map \| null | `{ tokenId: number, txHash: string, contractAddress: string, borrowerRef: string }` |
| `createdAt`, `updatedAt` | timestamp | |

`blockchain` map: `borrowerRef` is a `bytes32` hex string identifying the borrower on-chain without personal data (prototype: `keccak256(uid + appId)`). The loan note is owned by the bank's treasury wallet; **borrowers have no wallet**.

`property` map: `county` (string), `sizeSqm` (number), `bedrooms` (number), `type` (string), `berRating` (string, e.g. `A1` to `G`), `askingPrice` (number).

### `applications/{appId}/agentLogs/{logId}` (backend writes only)

| Field | Type | Notes |
|---|---|---|
| `agentName` | string | `Affordability` \| `Valuation` \| `MarketMacro` \| `UnderwritingStrategist` |
| `modelUsed` | string | e.g. `groq:llama-3.3-70b`, `ollama:llama3` |
| `reasoning` | string | Human-readable trail shown in the Audit Console |
| `output` | map | Structured result of the agent |
| `confidence` | number | 0 to 1 |
| `timestamp` | timestamp | |

### `applications/{appId}/documents/{docId}` (metadata only)

`fileName`, `fileType`, `storagePath` (string), `uploadedBy` (uid), `ocrExtractedData` (map, optional, for the OCR custom feature), `uploadedAt` (timestamp).

### `applications/{appId}/messages/{msgId}`

`senderId` (uid), `senderRole` (string), `text` (string), `timestamp` (timestamp), `read` (boolean).

### `payments/{paymentId}` (backend writes only)

`applicationId`, `userId`, `amount` (number, **cents**), `currency` (`eur`), `purpose` (`appraisal_fast_track` \| `verification_fee`), `provider` (`stripe` \| `paypal`), `status` (`pending` \| `succeeded` \| `failed`), `createdAt`.

### `reviews/{reviewId}`

`userId`, `rating` (number, 1 to 5), `comment` (string), `createdAt`.

### `supportTickets/{ticketId}`

`userId`, `subject`, `message`, `status` (`open` \| `resolved`), `createdAt`.

### `valuationChecks/{checkId}` (optional, history of fair-price queries)

`userId`, `property` (same map as above), `estimatedValue` (number), `createdAt`. Informational only; never used for lending decisions.

### `stressTests/{testId}` (underwriters only)

`createdBy` (uid), `rateShockBps` (number, 100 to 300), `portfolioSnapshot` (map), `results` (map), `createdAt`.

## 7. Required query shapes

Security rules reject queries that could return documents the user may not read, so clients **must** include these filters.

| Client | Query on `applications` |
|---|---|
| Mobile (borrower) | `where('borrowerId', '==', uid)` + `orderBy('createdAt', 'desc')` |
| Web (broker) | `where('brokerId', '==', uid)` + optional `status`, `riskTier`, `ltvBand` + `orderBy('createdAt', 'desc')` |
| Web (underwriter) | Any combination of `status`, `riskTier`, `ltvBand` + `orderBy('createdAt', 'desc')` |

Do not range-filter on `ltv`; filter on `ltvBand`. Indexes live in `firestore.indexes.json`. If a query throws a "requires an index" error, send the generated link to the AL-Core owner.

## 8. Open decisions (confirm as a team, then delete this section)

1. **`debts` meaning:** monthly repayments (assumed) or total outstanding balance?
2. **LTV formula:** `(askingPrice - deposit) / min(askingPrice, mlValuation) * 100` (assumed).
3. **DTI formula:** how is the new loan repayment included? Does it use the stressed rate?
4. **`riskTier` thresholds:** what LTV/DTI/likelihood values map to Low, Medium, High?
5. **`auditHash` payload:** exactly which fields, in what canonical form (sorted-key JSON, UTF-8)? The AI Engine and Ledger must produce the same hash, so write the rule here.
6. **AI trigger:** Flask Firestore listener on `status == 'Applied'` (assumed) or Cloud Functions?
7. **Broker-created applications:** can brokers create files for clients? Current rules say no.
8. **`borrowerRef` derivation:** `keccak256(uid + appId)` for the prototype. A production system would add a secret salt, since on-chain data cannot be erased later (GDPR). Ledger and AI Engine must use the same formula.
9. **Custom feature fields:** list any extra fields here (e.g. OCR output, `apr` adjustment for BER, amenity score).

## 9. Change log

| Date | Change | By |
|---|---|---|
| `<date>` | Initial schema | AL-Core |
