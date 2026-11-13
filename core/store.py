import json
import os

import firebase_admin
from fastapi import HTTPException
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore import SERVER_TIMESTAMP, transactional

# Log in to Firebase as the server, using the service account key
firebase_admin.initialize_app(
    credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
)
db = firestore.client()


def require_role(authorization, role):
    # Check the caller's Firebase login token and their role. Returns their user ID.
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing login token")
    try:
        uid = auth.verify_id_token(authorization.removeprefix("Bearer "))["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired login token")

    user = db.collection("users").document(uid).get()
    if not user.exists or user.to_dict().get("role") != role:
        raise HTTPException(status_code=403, detail=f"Only a {role} can do this")
    return uid


@transactional
def claim(transaction, ref, allowed_statuses, new_status):
    # Read the application and change its status in one all-or-nothing step.
    # If two requests arrive at the same time, only one of them gets through.
    snapshot = ref.get(transaction=transaction)
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Application not found")

    application = snapshot.to_dict()
    if application.get("status") not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=f"Not allowed while status is '{application.get('status')}'",
        )

    transaction.update(ref, {"status": new_status})
    return application