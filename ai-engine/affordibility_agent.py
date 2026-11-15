# The affordability agent usuing crewAi and groq
# The LLM doesnt do the maths it calls check_affordability() as a tool then explains it
# Needs a groq API key set as the environment variable GROQ_API_KEY do not harcode it in and put in on github
# Run with python affordability_agent.py

import os

from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool

from affordibility import check_affordability


# the docstring tells the LLM what the tool does and what to give it
@tool("Check affordability")
def affordability_tool(gross_income: float, net_monthly_income: float, monthly_debts: float,
                       price: float, deposit: float, interest_rate: float, term_years: int,
                       first_time_buyer: bool, adults: int, children: int) -> str:
    """Checks if a mortgage applicant can afford a loan under Central Bank of Ireland rules.
    gross_income is yearly, net_monthly_income and monthly_debts are per month, interest_rate
    is a percentage like 3.8. Returns PASS or FAIL with a reason for each check."""
    result = check_affordability(gross_income, net_monthly_income, monthly_debts, price, deposit,
                                 interest_rate, term_years, first_time_buyer, adults, children)
    return str(result)


# temperature=0 makes its answers consistent and its in openAIs format for connecting not claudes
llm = LLM( model="openai/openai/gpt-oss-120b", base_url="https://api.groq.com/openai/v1", api_key=os.environ["GROQ_API_KEY"], temperature=0,)
# the agent: who it is and how it should behave this is its prompt itll use each time to determine how it should behave
agent = Agent(
    role="Mortgage Affordability Analyst",
    goal="Decide whether an applicant can afford their mortgage and explain why to an underwriter",
    backstory="You are a careful credit analyst at an Irish bank. You never do the maths yourself you always use the Check affordability tool and base your answer only on what it returns. You quote the real figures in your explanation.",
    tools=[affordability_tool],
    llm=llm,
    verbose=True,  # prints the agents steps so you can see it using the tool
)

# an example application to assess
application = """
Gross yearly income: €95,000
Net monthly income: €5,900
Monthly debts: €250
House price: €420,000
Deposit: €42,000
Interest rate: 3.8%
Term: 30 years
First-time buyer: yes
Adults: 2, children: 1
"""

# the task = what the agent has to do with the application
task = Task(
    description=f"Assess this mortgage application using the Check affordability tool:\n"
                f"{application}\n"
                f"Give the decision exactly as the tool returns it PASS or FAIL, then "
                f"explain each check in plain English using the figures.",
    expected_output="The decision PASS or FAIL followed by a short explanation of each check.",
    agent=agent,
)

# a crew runs the task with one agent and one task it just runs it
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
print("\n agents Verdict")
print(result)