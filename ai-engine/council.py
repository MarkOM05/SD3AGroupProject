# the council three different llms each vote on the decision and the majority wins
# 2 cloud models groq and gemini plus 1 local model on ollama like the spec asks
# needs GROQ_API_KEY and GEMINI_API_KEY set and ollama running with llama3.2:3b

import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

VOTES = ["APPROVE", "REFER", "DECLINE"]
TIMEOUT = 300  # seconds to wait for a model before giving up on it


# makes the 3 models only when the council runs so the tests dont need keys
def make_models():
    from crewai import LLM
    return {
        "groq:gpt-oss-120b": LLM(model="openai/openai/gpt-oss-120b",
                                 base_url="https://api.groq.com/openai/v1",
                                 api_key=os.environ["GROQ_API_KEY"], temperature=0),
        "gemini:gemini-3.5-flash-lite": LLM(model="gemini/gemini-3.5-flash-lite",
                                            api_key=os.environ["GEMINI_API_KEY"], temperature=0),
        "ollama:llama3.2:3b": LLM(model="openai/llama3.2:3b", base_url="http://localhost:11434/v1",
                                  api_key="ollama", temperature=0),
    }


# the same question for every model
def make_question(affordability, valuation):
    return (f"You are on a mortgage credit committee at an Irish bank.\n\n"
            f"Affordability result: {affordability}\n\n"
            f"Valuation result: {valuation}\n\n"
            f"Vote APPROVE, REFER or DECLINE. REFER means a human underwriter should check it.\n"
            f"Reply with the vote on the first line then one sentence explaining why.")


# finds the vote in the models reply eg "DECLINE\nthe stress test failed"
def read_vote(reply):
    first_line = reply.strip().split("\n")[0].upper()
    for vote in VOTES:
        if vote in first_line:
            return vote
    return None  # the model didnt give a proper vote


# counts the votes and picks the majority
def count_votes(votes, rules_decision):
    valid = [v["vote"] for v in votes if v["vote"] is not None]

    # not enough models answered so trust the rules
    if len(valid) < 2:
        return rules_decision, "not enough models answered so the rules decision was used"

    winner, count = Counter(valid).most_common(1)[0]
    if count < 2:
        return "REFER", "the models disagreed so a human should check it"
    return winner, f"{count} of {len(valid)} models voted {winner}"


# asks one model and catches any errors so one broken model doesnt stop the council
def ask_model(name, llm, question):
    try:
        reply = llm.call(question)
        return {"model": name, "vote": read_vote(reply), "reply": reply}
    except Exception as error:
        return {"model": name, "vote": None, "reply": f"failed: {error}"}


# asks all 3 at the same time then counts the votes
def run_council(affordability, valuation, rules_decision, models=None):
    models = models or make_models()
    question = make_question(affordability, valuation)

    with ThreadPoolExecutor() as pool:
        jobs = {name: pool.submit(ask_model, name, llm, question) for name, llm in models.items()}
        votes = []
        for name, job in jobs.items():
            try:
                votes.append(job.result(timeout=TIMEOUT))
            except Exception:
                votes.append({"model": name, "vote": None, "reply": "timed out"})

    decision, summary = count_votes(votes, rules_decision)
    return {"decision": decision, "summary": summary, "votes": votes}

# turns the votes into agent logs with the fields from docs/schema.md
def council_logs(council):
    logs = []
    for vote in council["votes"]:
        # how many models agreed with this one eg 2 of 3 is 0.67
        agreed = sum(1 for v in council["votes"] if v["vote"] == vote["vote"])
        logs.append({
            "agentName": "UnderwritingStrategist",
            "modelUsed": vote["model"],
            # everything after the first line is the models reason
            "reasoning": vote["reply"].strip().split("\n", 1)[-1].strip(),
            "output": {"vote": vote["vote"], "councilDecision": council["decision"],
                       "councilSummary": council["summary"]},
            "confidence": round(agreed / len(council["votes"]), 2) if vote["vote"] else 0.0,
        })
    return logs