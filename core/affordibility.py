# The affordability calculations
# the agent calls check_affordability() as its tool

# Central Bank of Ireland mortgage rules
LTI_CAP_FIRST_TIME = 4.0   # first time buyers can borrow up to 4x gross income
LTI_CAP_OTHER = 3.5        # everyone else can borrow up to 3.5x
MAX_LTV = 0.90             # the loan can be at most 90% of the price, 10% deposit

# lenders own rules, assumptions not concrete
STRESS_BUFFER = 2.0          # test repayments at the interest rate plus 2 percentage points
MAX_REPAYMENT_SHARE = 0.35   # stressed repayment and debts at most 35% of net income
LIVING_COSTS = 1100          # € per month for the household

# defaults for things the user doesn't enter
DEFAULT_INTEREST_RATE = 3.8     # % a year, update to current typical rates
ASSUME_FIRST_TIME_BUYER = True

# rough Irish tax figures for a single PAYE employee, used to estimate net income
# APPROXIMATE: check against revenue.ie and update after each budget
STANDARD_RATE_BAND = 44000      # income taxed at 20%, above this 40%
TAX_CREDITS = 4000              # personal + employee credits
USC_EXEMPT_LIMIT = 13000        # no USC at or below this income
USC_BANDS = [                   # (upper limit of band, rate)
    (12012, 0.005),
    (28700, 0.02),
    (70044, 0.03),
    (float("inf"), 0.08),
]
PRSI_RATE = 0.0435
PRSI_THRESHOLD = 18304          # roughly €352 a week


# monthly mortgage repayment using the standard mortgage formula
def monthly_repayment(loan, interest_rate, term_years):
    months = term_years * 12
    monthly_rate = interest_rate / 100 / 12
    if monthly_rate == 0:
        return loan / months
    return loan * monthly_rate / (1 - (1 + monthly_rate) ** -months)


# rough take-home pay per month from gross yearly income
def estimate_net_monthly_income(gross_income):
    # income tax
    tax = min(gross_income, STANDARD_RATE_BAND) * 0.20
    tax += max(gross_income - STANDARD_RATE_BAND, 0) * 0.40
    tax = max(tax - TAX_CREDITS, 0)

    # USC
    usc = 0
    if gross_income > USC_EXEMPT_LIMIT:
        lower = 0
        for upper, rate in USC_BANDS:
            if gross_income > lower:
                usc += (min(gross_income, upper) - lower) * rate
            lower = upper

    # PRSI
    prsi = gross_income * PRSI_RATE if gross_income > PRSI_THRESHOLD else 0

    return (gross_income - tax - usc - prsi) / 12


# money left each month after debts and living costs, before the mortgage
def disposable_income(net_monthly_income, monthly_debts):
    return net_monthly_income - monthly_debts - LIVING_COSTS


def check_affordability(income, debts, deposit, propertyValue, termYears):
    # income = gross yearly income, debts = monthly debt repayments
    interest_rate = DEFAULT_INTEREST_RATE
    first_time_buyer = ASSUME_FIRST_TIME_BUYER
    net_monthly_income = estimate_net_monthly_income(income)

    loan = propertyValue - deposit
    reasons = []
    passed = True

    # check 1 loan to income
    lti = loan / income
    lti_cap = LTI_CAP_FIRST_TIME if first_time_buyer else LTI_CAP_OTHER
    if lti <= lti_cap:
        reasons.append(f"PASS: loan is {lti:.2f}x income, limit is {lti_cap}x")
    else:
        reasons.append(f"FAIL: loan is {lti:.2f}x income, over the {lti_cap}x limit")
        passed = False

    # check 2 loan to value, deposit must be at least 10%
    ltv = loan / propertyValue
    if ltv <= MAX_LTV:
        reasons.append(f"PASS: loan is {ltv:.0%} of the price, limit is {MAX_LTV:.0%}")
    else:
        reasons.append(f"FAIL: loan is {ltv:.0%} of the price, over the {MAX_LTV:.0%} limit")
        passed = False

    # check 3 stress test, can they still pay if rates rose 2 points
    repayment = monthly_repayment(loan, interest_rate, termYears)
    stressed_rate = interest_rate + STRESS_BUFFER
    stressed = monthly_repayment(loan, stressed_rate, termYears)
    share = (stressed + debts) / net_monthly_income
    if share <= MAX_REPAYMENT_SHARE:
        reasons.append(f"PASS: at {stressed_rate}% repayments are €{stressed:,.0f}/month, "
                       f"{share:.0%} of net income with debts, the lender's limit is {MAX_REPAYMENT_SHARE:.0%}")
    else:
        reasons.append(f"FAIL: at {stressed_rate}% repayments are €{stressed:,.0f}/month, "
                       f"{share:.0%} of net income with debts, over the lender's {MAX_REPAYMENT_SHARE:.0%} limit")
        passed = False

    # check 4 money left over after living costs, debts and the stressed repayment
    left_over = disposable_income(net_monthly_income, debts) - stressed
    if left_over >= 0:
        reasons.append(f"PASS: €{left_over:,.0f}/month left after living costs, debts "
                       f"and stressed repayments")
    else:
        reasons.append(f"FAIL: €{-left_over:,.0f}/month short after living costs, debts "
                       f"and stressed repayments")
        passed = False

    return {
        "decision": "PASS" if passed else "FAIL",
        "reasons": reasons,
        "loan": round(loan),
        "monthly_repayment": round(repayment),
        "stressed_repayment": round(stressed),
        "assumptions": [
            f"Interest rate of {interest_rate}%",
            "First-time buyer" if first_time_buyer else "Not a first-time buyer",
            f"Estimated take-home pay of €{net_monthly_income:,.0f}/month (single person, PAYE)",
            f"Living costs of €{LIVING_COSTS:,}/month",
        ],
    }


# testing
if __name__ == "__main__":
    result = check_affordability(income=25000, debts=250, deposit=40000,
                                 propertyValue=250000, termYears=30)
    print(result["decision"])
    for reason in result["reasons"]:
        print(" ", reason)
    for a in result["assumptions"]:
        print("  assumed:", a)