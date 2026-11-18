#takes other agents results and decides approve or decline or refer with a confidence level
import json
import os


# makes the final decision from the affordability and valuation results
# market is optional because the market agent isnt built until sprint 3
def make_decision(affordability, valuation, market=None):
    reasons = []

    # no valuation means we cant check the property so a human has to look at it
    if valuation is None:
        decision, confidence = "REFER", "LOW"
        reasons.append("no valuation result so the property price couldnt be checked")

    # cant afford it so decline no matter what the property is worth
    elif affordability["decision"] == "FAIL":
        decision, confidence = "DECLINE", "HIGH"
        reasons.append("the applicant failed the affordability checks")
        if valuation["verdict"] == "OVERPRICED":
            reasons.append("the property is also overpriced")

    # can afford it but the property is overpriced so the agents disagree
    elif valuation["verdict"] == "OVERPRICED":
        decision, confidence = "REFER", "MEDIUM"
        reasons.append("the applicant can afford it but the property looks overpriced")
        reasons.append("an underwriter should check the valuation before approving")

    # can afford it and the price is fair or good so everything agrees
    else:
        decision, confidence = "APPROVE", "HIGH"
        reasons.append("the applicant passed the affordability checks")
        reasons.append(f"the property is {valuation['verdict'].lower()}")

    # market isnt available yet so say so instead of pretending it was checked
    if market is None:
        reasons.append("market conditions not checked yet market agent comes in sprint 3")

    return {"decision": decision, "confidence": confidence, "reasons": reasons}


# puts everything into one structured credit memo
def make_credit_memo(application_id, affordability, valuation, decision, summary=""):
    return {
        "application_id": application_id,
        "decision": decision["decision"],
        "confidence": decision["confidence"],
        "reasons": decision["reasons"],
        "affordability": affordability,
        "valuation": valuation,
        "market": None,
        "summary": summary,  # the llms written explanation goes here
    }


# saves the memo as a json file so the web portal console can show it
def save_log(memo):
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{memo['application_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memo, f, indent=2)
    return path