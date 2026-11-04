# tests for the affordability calculations mostly the borderline cases
# run with pytest -v

from affordibility import check_affordability, monthly_repayment

# makes a normal couple that can afford it each test changes one thing so only one check gets tested
def application(**changes):
    details = dict(gross_income=100000, net_monthly_income=7000, monthly_debts=0,
                   price=375000, deposit=75000, interest_rate=3.5, term_years=30,
                   first_time_buyer=True, adults=2, children=0)
    details.update(changes)
    return check_affordability(**details)

def test_repayment_matches_known_value():
    # 300k over 30 years at 4% should be 1432.25 a month
    assert round(monthly_repayment(300000, 4.0, 30), 2) == 1432.25

def test_comfortable_application_passes():
    assert application()["decision"] == "PASS"

# loan to income tests limit is 4x for first time buyers and 3.5x for everyone else

def test_exactly_4x_income_passes():
    # 400k loan on 100k income is exactly 4x
    assert application(price=500000, deposit=100000)["decision"] == "PASS"

def test_just_over_4x_income_fails():
    # 401k loan is just over 4x
    assert application(price=501000, deposit=100000)["decision"] == "FAIL"


def test_second_time_buyer_has_lower_limit():
    # 3.8x is fine for first time buyer but over the 3.5x limit for anyone else
    assert application(price=475000, deposit=95000)["decision"] == "PASS"
    assert application(price=475000, deposit=95000, first_time_buyer=False)["decision"] == "FAIL"

# loan to value tests deposit has to be at least 10%
def test_exactly_10_percent_deposit_passes():
    assert application(price=300000, deposit=30000)["decision"] == "PASS"


def test_just_under_10_percent_deposit_fails():
    assert application(price=300000, deposit=29000)["decision"] == "FAIL"

# stress test repayments at the rate plus 2 has to be 35% or less of net income

def test_affordable_now_but_fails_stress_test():
    # about 30% at 3.5% but about 38% at 5.5% so it fails
    result = application(net_monthly_income=4000, price=330000, deposit=60000)
    assert result["decision"] == "FAIL"
    assert result["reasons"][2].startswith("FAIL")


def test_debts_can_tip_it_into_fail():
    # passes with no debts but fails with a 1000 a month car loan
    assert application(price=480000, deposit=100000)["decision"] == "PASS"
    assert application(price=480000, deposit=100000, monthly_debts=1000)["decision"] == "FAIL"

# money left over cant go below zero

def test_children_can_leave_too_little_left_over():
    # 4 kids adds enough living costs that theres nothing left
    result = application(net_monthly_income=5200, price=350000, deposit=100000, children=4)
    assert result["reasons"][3].startswith("FAIL")