# AL (Agentic Lender): Firestore Schema

**Owner:** AL-Core (team lead) | **Last updated:** 2026-10-27 | **Version:** 0.2

This file is the contract between AL-Mobile, AL-Web, AL-AI Engine and the Ledger. If a field is not listed here, do not rely on it. To change the schema, open a pull request that edits this file **and** `firestore.rules` / `firestore.indexes.json` **and** `al-core/models.py` (the Python mirror used by the API and the seed script). Only the AL-Core owner deploys.

## 1. Project facts

| Item | Value |
|---|---|
| Firebase project ID | `<fill in>` |
| Firestore location | `europe-west1` (permanent) |
| Auth providers | Email/Password, Google |
| Storage bucket (files) | `<fill in>`; Firestore holds metadata only |
| Firebase plan | Spark (free) assumed: no Cloud Functions, and Cloud Storage needs the Blaze plan (see §8) |

## 2. Conventions

- Field names are `camelCase`; collection names are plural `camelCase`.
- Dates and times are Firestore **Timestamp** values, never strings.
- Money is a **number in EUR** (whole euros) unless stated; payment `amount` is in **cents**.
- Percentages (`ltv`, `dti`, `apr`) are numbers like `76.6`, **not** `0.766`.
- `approvalLikelihood` is a number from `0` to `1`.
- `apr` is stored as a percent (`4.35`). The Ledger converts it to basis points for the contract with `round(apr * 100)`; always round, because `4.35 * 100` is not exactly `435` in floating point.
- `users/{uid}` uses the Firebase Auth UID as the document ID.
- Every `applications` write sets `updatedAt`.
- Use `null` for "not yet known"; do not use empty strings.
- The AL-Core API (FastAPI) uses the same field names in JSON. Timestamps in API responses are ISO 8601 UTC strings; Firestore itself always stores Timestamp values. The API's live contract is its `/docs` page.

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

An application can also end at `Declined` (from `AI Deliberated`). `Declined` and `Closed` are terminal.

| Transition | Set by | How |
|---|---|---|
| (create) → `Applied` | Mobile (or Web for broker-created files, if agreed) | Client write; rules require `status == 'Applied'` (see §5) |
| `Applied` → `AI Deliberated` | AI Engine | Admin SDK, after writing valuation fields and agentLogs. Started by the client calling `POST /applications/{appId}/deliberate` after the create (no Firestore listener; see §8) |
| `AI Deliberated` → `Underwriter Approved` | Web (underwriter) | `POST /applications/{appId}/approve` (Admin SDK): checks the caller's role and the current status, then records sign-off |
| `Underwriter Approved` → `Funded` | Ledger / backend | Same `/approve` call: mints, writes `blockchain` + `auditHash`, then sets `Funded`. If minting fails the status stays `Underwriter Approved` and `/approve` can be retried |
| `AI Deliberated` → `Declined` | Web (underwriter) | Client write with `decision = 'Decline'`; rules enforce role and forward-only |
| `Funded` → `Closed` | Web (underwriter) | Client write |

## 5. Who writes what

| Data | Written by |
|---|---|
| Application inputs (`income`, `debts`, `deposit`, `termYears`, `property`) | Mobile / Web |
| `mlValuation`, `ltv`, `ltvBand`, `dti`, `approvalLikelihood`, `riskTier`, `apr`, `creditMemo`, initial `decision`, `agentLogs` | AI Engine |
| `decision` override, status → `Declined` / `Closed` | Web (underwriter) |
| status → `Underwriter Approved` / `Funded`, `blockchain`, `auditHash` | Ledger / backend (via `POST /applications/{appId}/approve`) |
| `payments` | Backend, after Stripe/PayPal confirms |
| `messages`, `reviews`, `supportTickets`, `documents` metadata | Clients |
| `stressTests` | Web (underwriter) |
| `valuationChecks` (optional) | Backend, from `POST /valuation` for signed-in callers |

**Fields a client may never supply on application create:** `mlValuation`, `ltv`, `ltvBand`, `dti`, `approvalLikelihood`, `riskTier`, `decision`, `apr`, `creditMemo`, `auditHash`, `blockchain`.

**Fields a client may only set to a fixed value on create** (enforce in `firestore.rules`): `status == 'Applied'`, `borrowerId == request.auth.uid`, `brokerId == users/{uid}.assignedBrokerId` (or `null` if the user has none), `createdAt == request.time`.

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
| `brokerId` | string \| null | Auth uid of assigned broker. Copied from `users/{uid}.assignedBrokerId` at creation; `null` if the borrower has no broker |
| `loanType` | string | `mortgage` \| `heloc` |
| `income` | number | Gross annual household income |
| `debts` | number | Monthly repayments on existing debts *(see open decisions)* |
| `deposit` | number | |
| `termYears` | number | |
| `property` | map | See below |
| `status` | string | `Applied` \| `AI Deliberated` \| `Underwriter Approved` \| `Funded` \| `Closed` \| `Declined` (see lifecycle) |
| `mlValuation` | number | AI Engine |
| `ltv` | number | Percent, AI Engine |
| `ltvBand` | string | `<=60` \| `60-80` \| `>80`; derived from `ltv` for indexed filtering |
| `dti` | number | Percent, AI Engine |
| `approvalLikelihood` | number | 0 to 1 |
| `riskTier` | string | `Low` \| `Medium` \| `High` |
| `decision` | string \| null | `Approve` \| `Conditionally Approve` \| `Decline` |
| `apr` | number \| null | Percent, e.g. `4.35` (the Ledger converts to basis points, see conventions) |
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

`senderId` (uid), `senderRole` (`borrower` \| `broker` \| `underwriter`), `text` (string), `timestamp` (timestamp), `read` (boolean).

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
6. **AI trigger:** v0.2 proposes an explicit `POST /applications/{appId}/deliberate` call instead of a Firestore listener (needs an always-on process, which a free host that sleeps when idle can't give) or Cloud Functions (paid Blaze plan only). Confirm, or name the alternative.
7. **Broker-created applications:** can brokers create files for clients? Current rules say no.
8. **`borrowerRef` derivation:** `keccak256(uid + appId)` for the prototype. A production system would add a secret salt, since on-chain data cannot be erased later (GDPR). Ledger and AI Engine must use the same formula.
9. **Custom feature fields:** list any extra fields here (e.g. OCR output, `apr` adjustment for BER, amenity score).
10. **Approve flow:** v0.2 sends sign-off and minting through `POST /applications/{appId}/approve` (see §4). If Web writes the status directly instead, something else has to trigger the mint.
11. **`Declined` status:** added in v0.2 because §4 had no end state for a Decline decision. Confirm the name and whether the pipeline view should show it.
12. **Conditional approvals:** where are the conditions stored and who marks them met? Suggest a `conditions` array of strings written by the AI Engine and shown in the Web loan file.
13. **File uploads:** Cloud Storage for Firebase needs the Blaze (pay-as-you-go, card required) plan. Enable it with a budget alert, or keep `documents` as metadata plus `ocrExtractedData` and skip real uploads?

## 9. Change log

| Date | Change | By |
|---|---|---|
| `<date>` | Initial schema | AL-Core |
| 2026-10-27 | v0.2: added `Declined` status; `brokerId` nullable plus create-time rules; AI and approve flows go through the API (no listener or Functions); `apr` basis-point note; `senderRole` values; `valuationChecks` writer; `models.py` added to the sync rule | AL-Core |
