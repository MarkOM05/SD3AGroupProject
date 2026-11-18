# tests for the underwriting strategist mostly when the agents disagree
# run with pytest -v

from underwriting import make_credit_memo, make_decision

# sample results from the other agents
can_afford = {"decision": "PASS", "reasons": []}
cant_afford = {"decision": "FAIL", "reasons": []}
fair = {"verdict": "FAIR", "ltv": 85}
overpriced = {"verdict": "OVERPRICED", "ltv": 96}
underpriced = {"verdict": "UNDERPRICED", "ltv": 80}


def test_everything_good_approves():
    result = make_decision(can_afford, fair)
    assert result["decision"] == "APPROVE"
    assert result["confidence"] == "HIGH"


def test_good_deal_approves():
    assert make_decision(can_afford, underpriced)["decision"] == "APPROVE"


def test_cant_afford_declines():
    assert make_decision(cant_afford, fair)["decision"] == "DECLINE"


# conflicting results

def test_can_afford_but_overpriced_refers():
    # agents disagree so a human checks it
    result = make_decision(can_afford, overpriced)
    assert result["decision"] == "REFER"
    assert result["confidence"] == "MEDIUM"


def test_cant_afford_even_if_good_deal_declines():
    # a cheap house doesnt help if they cant pay
    assert make_decision(cant_afford, underpriced)["decision"] == "DECLINE"


def test_missing_valuation_refers():
    result = make_decision(can_afford, None)
    assert result["decision"] == "REFER"
    assert result["confidence"] == "LOW"


def test_says_market_wasnt_checked():
    reasons = make_decision(can_afford, fair)["reasons"]
    assert any("market" in r for r in reasons)


def test_memo_has_everything_the_console_needs():
    decision = make_decision(can_afford, fair)
    memo = make_credit_memo("APP-001", can_afford, fair, decision, "summary text")
    for field in ["application_id", "decision", "confidence", "reasons",
                  "affordability", "valuation", "market", "summary"]:
        assert field in memo