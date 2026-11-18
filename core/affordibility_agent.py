# The affordability agent using crewAI and groq
# The LLM doesn't do the maths, it calls check_affordability() as a tool then explains it
# Needs a groq API key set as the environment variable GROQ_API_KEY, do not hardcode it or put it on github

import os

from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool

from affordibility import check_affordability


# the docstring tells the LLM what the tool does and what to give it
@tool("Check affordability")
def affordability_tool(income: float, debts: float, deposit: float,
                       property_value: float, term_years: int) -> str:
    """Checks if a mortgage applicant can afford a loan under Central Bank of Ireland rules.
    income is gross yearly income in euro, debts is total monthly debt repayments in euro,
    deposit and property_value are in euro, term_years is the mortgage length in years.
    Returns PASS or FAIL with a reason for each check, the loan amount, monthly and stressed
    repayments, and the assumptions used (interest rate, first-time buyer, estimated
    take-home pay, living costs)."""
    result = check_affordability(income=income, debts=debts, deposit=deposit,
                                 propertyValue=property_value, termYears=term_years)
    return str(result)


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it as an environment variable.")
    # temperature=0 makes its answers consistent, it uses OpenAI's format for connecting
    return LLM(model="openai/openai/gpt-oss-120b", base_url="https://api.groq.com/openai/v1",
               api_key=api_key, temperature=0)


# builds a fresh agent and crew for each application and returns the agent's explanation
def run_affordability_agent(income, debts, deposit, property_value, term_years, verbose=False):
    agent = Agent(
        role="Mortgage Affordability Analyst",
        goal="Decide whether an applicant can afford their mortgage and explain why to an underwriter",
        backstory="You are a careful credit analyst at an Irish bank. You never do the maths yourself, "
                  "you always use the Check affordability tool and base your answer only on what it "
                  "returns. You quote the real figures in your explanation and clearly state the "
                  "assumptions the tool made, because the applicant did not provide them.",
        tools=[affordability_tool],
        llm=get_llm(),
        verbose=verbose,
    )

    application = (
        f"Gross yearly income: €{income:,}\n"
        f"Monthly debts: €{debts:,}\n"
        f"House price: €{property_value:,}\n"
        f"Deposit: €{deposit:,}\n"
        f"Term: {term_years} years\n"
    )

    task = Task(
        description=f"Assess this mortgage application using the Check affordability tool:\n"
                    f"{application}\n"
                    f"Give the decision exactly as the tool returns it, PASS or FAIL, then "
                    f"explain each check in bullet points using the figures. Finish by listing "
                    f"the assumptions the tool made.",
        expected_output="The decision PASS or FAIL, a short explanation of each check, "
                        "and the assumptions used.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task])
    return crew.kickoff().raw


# run directly for testing: python affordability_agent.py
if __name__ == "__main__":
    print(run_affordability_agent(income=95000, debts=250, deposit=42000,
                                  property_value=420000, term_years=30, verbose=True))