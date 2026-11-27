# saves the committees results to firestore in the places docs/schema.md says
# the results go onto applications/{appId} and each agents reasoning goes in its agentLogs
# needs FIREBASE_KEY_PATH in the run configuration pointing at the key file
# never put the key file in the project folder or on github

import os

# the schema uses different words to our rules
DECISION_NAMES = {"APPROVE": "Approve", "REFER": "Conditionally Approve", "DECLINE": "Decline"}

# the schema wants confidence as a number from 0 to 1
CONFIDENCE_NUMBERS = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}

# connects the first time its needed so the tests dont need the key
db = None


def connect():
    global db  # global lets this function change the variable above
    if db is None:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(os.environ["FIREBASE_KEY_PATH"]))
        db = firestore.client()
    return db


# the schema groups ltv into bands so the portal can filter by them
def ltv_band(ltv):
    if ltv <= 60:
        return "<=60"
    if ltv <= 80:
        return "60-80"
    return ">80"


# the fields the ai engine adds onto the application
def application_fields(memo):
    return {
        "mlValuation": memo["valuation"]["mlValuation"],
        "ltv": memo["valuation"]["ltv"],
        "ltvBand": ltv_band(memo["valuation"]["ltv"]),
        "decision": DECISION_NAMES[memo["decision"]],
        "creditMemo": memo["summary"],
        "status": "AI Deliberated",
    }


# one log for each agent plus one for each council vote
def agent_logs(memo, council_logs):
    logs = {
        "affordability": {
            "agentName": "Affordability",
            "modelUsed": "rules",  # its a calculation no llm
            "reasoning": "\n".join(memo["affordability"]["reasons"]),
            "output": memo["affordability"],
            "confidence": 1.0,
        },
        "valuation": {
            "agentName": "Valuation",
            "modelUsed": "ml:random-forest",
            "reasoning": "\n".join(memo["valuation"]["reasons"]),
            "output": memo["valuation"],
            "confidence": 0.8,  # the model is about 20% off on average
        },
        "strategist": {
            "agentName": "UnderwritingStrategist",
            "modelUsed": "gemini:gemini-3.5-flash-lite",
            "reasoning": "\n".join(memo["reasons"]),
            "output": {"decision": memo["decision"], "confidence": memo["confidence"]},
            "confidence": CONFIDENCE_NUMBERS[memo["confidence"]],
        },
    }
    for log in council_logs:
        logs["council-" + log["modelUsed"]] = log
    return logs


# writes everything to firestore
# uses update so it only works on an application that already exists and never makes a fake one
def save_to_firestore(app_id, memo, council_logs):
    from firebase_admin import firestore
    app_ref = connect().collection("applications").document(app_id)

    fields = application_fields(memo)
    fields["updatedAt"] = firestore.SERVER_TIMESTAMP
    app_ref.update(fields)

    # the log names are the document ids so running it again replaces the old logs
    for name, log in agent_logs(memo, council_logs).items():
        log["timestamp"] = firestore.SERVER_TIMESTAMP
        app_ref.collection("agentLogs").document(name).set(log)

    return f"applications/{app_id}"