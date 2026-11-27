# tests for saving to firestore these check the data matches docs/schema.md
# they dont connect to firestore so they dont need the key
# run with pytest -v

from firestore_save import agent_logs, application_fields, ltv_band

memo = {"application_id": "APP-001", "decision": "REFER", "confidence": "MEDIUM",
        "reasons": ["the applicant failed the affordability checks"],
        "affordability": {"decision": "FAIL", "reasons": ["PASS: loan is 3.98x income", "FAIL: stress test"]},
        "valuation": {"mlValuation": 384113, "ltv": 98.4, "reasons": ["loan is 98.4% of the value"]},
        "market": None, "summary": "the credit memo text"}

council_logs = [{"agentName": "UnderwritingStrategist", "modelUsed": "groq:gpt-oss-120b",
                 "reasoning": "too risky", "output": {"vote": "DECLINE"}, "confidence": 0.33}]


# the application fields

def test_ltv_bands():
    assert ltv_band(60) == "<=60"
    assert ltv_band(80) == "60-80"
    assert ltv_band(98.4) == ">80"


def test_decision_uses_the_schema_words():
    assert application_fields(memo)["decision"] == "Conditionally Approve"


def test_application_has_the_schema_fields():
    fields = application_fields(memo)
    assert fields["mlValuation"] == 384113
    assert fields["ltvBand"] == ">80"
    assert fields["creditMemo"] == "the credit memo text"
    assert fields["status"] == "AI Deliberated"


# the agent logs

def test_one_log_per_agent_and_per_vote():
    logs = agent_logs(memo, council_logs)
    assert list(logs) == ["affordability", "valuation", "strategist", "council-groq:gpt-oss-120b"]


def test_logs_have_the_schema_fields():
    for log in agent_logs(memo, council_logs).values():
        assert set(log) == {"agentName", "modelUsed", "reasoning", "output", "confidence"}
        assert 0 <= log["confidence"] <= 1