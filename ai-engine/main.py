import json
import os
from pathlib import Path

import httpx
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AL-AI Engine")

OLLAMA_URL = os.environ["OLLAMA_URL"]
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
DEPLOYMENT_FILE = os.environ.get("DEPLOYMENT_FILE", "/shared/deployment.json")
AVM_PATH = Path("models/avm.joblib")

_avm = None


def get_avm():
    """Load the trained sklearn Pipeline (preprocessing + regressor) once."""
    global _avm
    if _avm is None:
        if not AVM_PATH.exists():
            raise HTTPException(503, "Valuation model not trained yet: models/avm.joblib missing")
        _avm = joblib.load(AVM_PATH)
    return _avm


class PropertySpec(BaseModel):
    county: str
    floor_area_sqm: float
    bedrooms: int
    property_type: str
    ber_rating: str


@app.get("/health")
def health():
    deployment = None
    if Path(DEPLOYMENT_FILE).exists():
        deployment = json.loads(Path(DEPLOYMENT_FILE).read_text()).get("address")
    return {"status": "ok", "avm_loaded": AVM_PATH.exists(), "loan_contract": deployment}


@app.post("/valuation")
def valuation(spec: PropertySpec):
    # Column names must match what your training pipeline expects
    df = pd.DataFrame([spec.model_dump()])
    price = float(get_avm().predict(df)[0])
    return {"estimated_value_eur": round(price, 2)}


@app.post("/llm/local-test")
async def local_llm_test(prompt: str = "Say hello in one sentence."):
    """Smoke test that FastAPI can reach the Ollama container."""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        r.raise_for_status()
        return {"response": r.json()["response"]}


# TODO: /deliberate endpoint -> run Affordability, Valuation, Market & Macro,
# and Underwriting Strategist agents, return the credit memo + decision trail.
