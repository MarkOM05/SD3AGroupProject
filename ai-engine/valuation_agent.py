# the valuation agent usuing crewai and a local llm running on ollama
# the llm doesnt do the maths it calls check_valuation() as a tool then explains it
# needs ollama running with the model downloaded  ollama pull qwen3:8b
# no api key needed because the model runs on this computer

from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool

from valuation import check_valuation


# the docstring tells the llm what the tool does and what to give it
@tool("Check valuation")
def valuation_tool(county: str, sizeSqm: int, bedrooms: int, type: str, berRating: str,askingPrice: int, deposit: int) -> str:
    """Estimates what a property is worth using the trained valuation model and compares it
     to the asking price. county is one of the 26 irish counties like Cork. sizeSqm is the
     floor area in square metres. type is one of Apartment, Bungalow, Detached, Duplex,
     End of Terrace, Semi-D, Studio, Terrace or Townhouse. berRating is a grade like B2.
     Returns OVERPRICED, FAIR or UNDERPRICED with the estimate, the gap and the LTV."""
    result = check_valuation(county, sizeSqm, bedrooms, type, berRating, askingPrice, deposit)
    return str(result)


# ollama runs on this computer and accepts requests in openais format like groq does
# the api key can be anything ollama doesnt check it but crewai needs one
llm = LLM(model="openai/qwen3:8b", base_url="http://localhost:11434/v1", api_key="ollama",temperature=0)

# the agent who it is and how it should behave this is its prompt
agent = Agent(
    role="Property Valuation Analyst",
    goal="Decide whether a property is fairly priced and explain why to a bank underwriter",
    backstory="You are a careful property valuer at an Irish bank. You never guess a "
              "property's value yourself you always use the Check valuation tool and base "
              "your answer only on what it returns. You quote the real figures and remind "
              "the underwriter the estimate is a guide not an exact price.",
    tools=[valuation_tool],
    llm=llm,
    verbose=True,  # prints the agents steps so you can see it using the tool
)

# an example property with the same fields the app sends
property_details = """
County: Cork
Floor area: 110 square metres
Bedrooms: 3
Property type: Semi-D
BER: C1
Asking price: €420,000
Deposit: €42,000
"""

# the task what the agent has to do with the property
task = Task(
    description=f"Value this property using the Check valuation tool:\n"
                f"{property_details}\n"
                f"Give the verdict exactly as the tool returns it OVERPRICED FAIR or "
                f"UNDERPRICED then explain it in plain English using the figures, "
                f"including the LTV.",
    expected_output="The verdict followed by a short explanation of the estimate, the gap "
                    "and the LTV.",
    agent=agent,
)

# a crew runs the task with one agent and one task it just runs it
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
print("\n agents verdict")
print(result)