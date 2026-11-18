# quick test to check gemini is set up and the key works
import os
from crewai import LLM

# passing the key system variable directly so crewai cant pick up a different google api key which may be needed later for firebase
llm = LLM(model="gemini/gemini-3.5-flash-lite", api_key=os.environ["GEMINI_API_KEY"], temperature=0)

print(llm.call("Say hello in one short sentence"))