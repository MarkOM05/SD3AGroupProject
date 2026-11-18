# the underwriting strategist agent usuing crewai and gemini
# the rules in underwriting.py make the decision then the llm writes the credit memo explaining it
# needs GEMINI_API_KEY set as an environment variable

import os

from crewai import LLM, Agent, Crew, Task

from affordibility import check_affordability
from underwriting import make_credit_memo, make_decision, save_log

# example application same one as the affordability agent
application = dict(gross_income=95000, net_monthly_income=5900, monthly_debts=250,
                   price=420000, deposit=42000, interest_rate=3.8, term_years=30,
                   first_time_buyer=True, adults=2, children=1)

# 1 get the other agents results
affordability = check_affordability(**application)

# sample valuation result swap this for the real valuation agent once its built
valuation = {"asking_price": 420000, "valuation": 425000, "verdict": "FAIR", "ltv": 88.9}

# 2 the rules make the decision
decision = make_decision(affordability, valuation)

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
                f"Start with the decision and confidence exactly as given. Then explain in plain "
                f"English why using the figures, and list any risks the underwriter should know.",
    expected_output="A short credit memo starting with the decision and confidence, then the "
                    "reasons and risks.",
    agent=agent,
)

crew = Crew(agents=[agent], tasks=[task])
summary = str(crew.kickoff())

# 4 save everything so the web portal can show it
memo = make_credit_memo("APP-001", affordability, valuation, decision, summary)
path = save_log(memo)

print("\n strategists decision:", decision["decision"], "confidence:", decision["confidence"])
print(" credit memo saved to", path)