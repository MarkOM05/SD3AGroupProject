# sends the underwriting agents json to firestore
# needs FIREBASE_KEY_PATH in the run configuration pointing at the key file
# never put the key file in the project folder or on github

import os
import firebase_admin
from firebase_admin import credentials, firestore

# only log in once even if this gets called again
if not firebase_admin._apps:
    key = credentials.Certificate(os.environ["FIREBASE_KEY_PATH"])
    firebase_admin.initialize_app(key)

db = firestore.client()


# saves the memo under its application id so the portal can find it
def save_to_firestore(memo):
    db.collection("creditMemos").document(memo["application_id"]).set(memo)
    return f"creditMemos/{memo['application_id']}"