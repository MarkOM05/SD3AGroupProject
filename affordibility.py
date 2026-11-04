# The affordability calculations
# the agent calls check_affordability() as its tool

# Central Bank of Ireland mortgage rules
LTI_CAP_FIRST_TIME = 4.0   # first time buyers can borrow up to 4x gross income
LTI_CAP_OTHER = 3.5        # everyone else can borrow up to 3.5x
MAX_LTV = 0.90             # the loan can be at most 90% of the price 10% deposit

# lenders own rules assumptions not concrete
STRESS_BUFFER = 2.0          # test repayments at the interest rate plus 2 percentage points
MAX_REPAYMENT_SHARE = 0.35   # stressed repayment and debts at most 35% of net income
LIVING_COST_PER_ADULT = 1100     # € per month
LIVING_COST_PER_CHILD = 450      # € per month


# monthly mortgage repayment using a standard mortgage formula I found online
def monthly_repayment(loan, interest_rate, term_years):
    months = term_years * 12
    monthly_rate = interest_rate / 100 / 12
    if monthly_rate == 0:
        return loan / months
    return loan * monthly_rate / (1 - (1 + monthly_rate) ** -months)


# money left each month after debts and living costs before the mortgage comes knocking
def disposable_income(net_monthly_income, monthly_debts, adults, children):
    living_costs = adults * LIVING_COST_PER_ADULT + children * LIVING_COST_PER_CHILD
    return net_monthly_income - monthly_debts - living_costs


def check_affordability(gross_income, net_monthly_income, monthly_debts, price, deposit, interest_rate, term_years, first_time_buyer, adults=1, children=0):
    loan = price - deposit
    reasons = []
    passed = True

    #check 1 loan to income
    lti = loan / gross_income
    lti_cap = LTI_CAP_FIRST_TIME if first_time_buyer else LTI_CAP_OTHER
    if lti <= lti_cap:
        reasons.append(f"PASS: loan is {lti:.2f}x income, limit is {lti_cap}x")
    else:
        reasons.append(f"FAIL: loan is {lti:.2f}x income, over the {lti_cap}x limit")
        passed = False

    # check 2 loan to value checking if deposit is at least 10%
    ltv = loan / price
    if ltv <= MAX_LTV:
        reasons.append(f"PASS: loan is {ltv:.0%} of the price limit is {MAX_LTV:.0%}")
    else:
        reasons.append(f"FAIL: loan is {ltv:.0%} of the price over the {MAX_LTV:.0%} limit")
        passed = False

    # check 3 stress test can they still pay if rates went up 2 points this is for added security
    repayment = monthly_repayment(loan, interest_rate, term_years)
    stressed_rate = interest_rate + STRESS_BUFFER
    stressed = monthly_repayment(loan, stressed_rate, term_years)
    share = (stressed + monthly_debts) / net_monthly_income
    if share <= MAX_REPAYMENT_SHARE:
        reasons.append(f"PASS: at {stressed_rate}% repayments are €{stressed:,.0f}/month, "f"{share:.0%} of net income with debts, the lenders limit is {MAX_REPAYMENT_SHARE:.0%}")
    else:
        reasons.append(f"FAIL: at {stressed_rate}% repayments are €{stressed:,.0f}/month, "f"{share:.0%} of net income with debts, over the lenders  {MAX_REPAYMENT_SHARE:.0%} limit")
        passed = False

    # check 4 money left over after living costs, debts, and the stressed repayment
    left_over = disposable_income(net_monthly_income, monthly_debts, adults, children) - stressed
    if left_over >= 0:
        reasons.append(f"PASS: €{left_over:,.0f}/month left after living costs, debts "f"and stressed repayments")
    else:
        reasons.append(f"FAIL: €{-left_over:,.0f}/month short after living costs, debts "f"and stressed repayments")
        passed = False

    return {
        "decision": "PASS" if passed else "FAIL",
        "reasons": reasons,
        "loan": round(loan),
        "monthly_repayment": round(repayment),
        "stressed_repayment": round(stressed),
    }


# testing
if __name__ == "__main__":
    result = check_affordability(gross_income=95000, net_monthly_income=5900, monthly_debts=250,
                                 price=420000, deposit=42000, interest_rate=3.8, term_years=30,
                                 first_time_buyer=True, adults=2, children=1)

    print(result["decision"])
    for reason in result["reasons"]:
        print(" ", reason)