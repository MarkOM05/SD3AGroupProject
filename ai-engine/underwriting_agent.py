# the underwriting strategist agent usuing crewai and gemini
# the rules in underwriting.py make the decision the council of 3 models checks it then gemini writes the credit memo
# needs GEMINI_API_KEY GROQ_API_KEY and FIREBASE_KEY_PATH set and ollama running

import os

from crewai import LLM, Agent, Crew, Task

from affordibility import check_affordability
from underwriting import make_credit_memo, make_decision, save_log
from valuation import check_valuation
from firestore_save import save_to_firestore
from council import run_council

# example application same one as the affordability agent
application = dict(gross_income=95000, net_monthly_income=5900, monthly_debts=250,
                   price=420000, deposit=42000, interest_rate=3.8, term_years=30,
                   first_time_buyer=True, adults=2, children=1)

# 1 get the other agents results
affordability = check_affordability(**application)

#calls valuation agent with hardcoded data
valuation = check_valuation(county="Cork", sizeSqm=110, bedrooms=3, type="Semi-D",
                            berRating="C1", askingPrice=application["price"],
                            deposit=application["deposit"])

# 2 the rules make the decision
decision = make_decision(affordability, valuation)

# the council of 3 models votes on it too
council = run_council(affordability, valuation, decision["decision"])
print("council:", council["summary"])

# if the council disagrees with the rules a human should check it
if council["decision"] != decision["decision"]:
    decision["decision"] = "REFER"
    decision["confidence"] = "MEDIUM"
    decision["reasons"].append(f"the council voted {council['decision']} which disagrees with the rules")

# 3 gemini writes the credit memo explaining the decision
# flash lite because the free tier allows 500 requests a day instead of 20
llm = LLM(model="gemini/gemini-3.5-flash-lite", api_key=os.environ["GEMINI_API_KEY"], temperature=0)

agent = Agent(
    role="Underwriting Strategist",
    goal="Explain the committees lending decision in a clear credit memo for a bank underwriter",
    backstory="You are a senior underwriter at an Irish bank. You read the results from the "
              "affordability and valuation agents and the final decision. You never change the "
              "decision you explain it using the real figures and point out any risks.",
    llm=llm,
    verbose=True,
)

task = Task(
    description=f"Write a short credit memo for this mortgage application.\n\n"
                f"Affordability result: {affordability}\n\n"
                f"Valuation result: {valuation}\n\n"
                f"Final decision: {decision}\n\n"
                f"Start with the decision and confidence exactly as given. " 
                f"mlValuation is the machine learning models estimate of the property value not a surveyors valuation. "
                f"The loan amount is in the affordability result use that exact figure. "
                f"Then explain in plain English why using the figures, and list any risks the underwriter should know.",
    expected_output="A short credit memo starting with the decision and confidence, then the "
                    "reasons and risks.",
    agent=agent,
)

crew = Crew(agents=[agent], tasks=[task])
summary = str(crew.kickoff())

# 4 save everything so the web portal can show it
memo = make_credit_memo("APP-001", affordability, valuation, decision, summary)
memo["council"] = council
path = save_log(memo)
# send the same json to firestore
print("saved to firestore at", save_to_firestore(memo))

print("\n strategists decision:", decision["decision"], "confidence:", decision["confidence"])
print(" credit memo saved to", path)