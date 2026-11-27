# the valuation agents calculations no llm here just the model and the maths so it can be tested
# uses the trained model to predict a fair price then compares it to the asking price
# takes the same fields the mobile app and website send county sizeSqm bedrooms type berRating

import joblib
import pandas as pd

from data import BER_SCORE

# how far the asking price can be from the models estimate and still count as fair
# the model is about 20% off on average so anything inside that is too close to call
FAIR_RANGE = 0.20

# central bank limit the loan can be at most 90% of the property value
MAX_LTV = 90

# the app doesnt send latitude and longitude so we use the middle of the county instead
# these are the median location of each countys houses in the cleaned daft data
COUNTY_CENTRES = {
    "Carlow": (52.8267, -6.9085), "Cavan": (53.9687, -7.3523), "Clare": (52.8065, -8.9633),
    "Cork": (51.8830, -8.5040), "Donegal": (54.9406, -7.7987), "Dublin": (53.3449, -6.2579),
    "Galway": (53.2943, -8.9481), "Kerry": (52.1453, -9.6975), "Kildare": (53.2326, -6.6871),
    "Kilkenny": (52.6457, -7.2517), "Laois": (53.0376, -7.2955), "Leitrim": (54.0198, -8.0003),
    "Limerick": (52.6284, -8.6420), "Longford": (53.7257, -7.7673), "Louth": (53.8485, -6.3667),
    "Mayo": (53.8577, -9.2199), "Meath": (53.6336, -6.5479), "Monaghan": (54.1204, -6.8491),
    "Offaly": (53.2779, -7.4870), "Roscommon": (53.7737, -8.2754), "Sligo": (54.2519, -8.4911),
    "Tipperary": (52.6166, -7.8407), "Waterford": (52.1819, -7.1404),
    "Westmeath": (53.4988, -7.3920), "Wexford": (52.3896, -6.4904), "Wicklow": (53.0101, -6.1219),
}

# the app uses some different names for property types than the daft data did
TYPE_NAMES = {"Terraced": "Terrace", "Semi-Detached": "Semi-D", "Semi-detached": "Semi-D"}

# the model and preprocessor only get loaded the first time theyre needed
# so the tests can run without loading the big model file
model = None
preprocessor = None


def load_model():
    global model, preprocessor  # global lets this function change the variables above
    if model is None:
        preprocessor = joblib.load("data/processed/preprocessor.joblib")
        model = joblib.load("models/valuation_model.joblib")


# turns the apps fields into one row with the column names the model was trained on
def prepare_house(county, sizeSqm, bedrooms, type, berRating, bathrooms=None,
                  latitude=None, longitude=None):
    county = county.strip().title()  # "dublin" becomes "Dublin"

    # use the exact location if we have it otherwise the middle of the county
    if latitude is None or longitude is None:
        latitude, longitude = COUNTY_CENTRES.get(county, (None, None))

    return pd.DataFrame([{
        "county": county,
        "floor_area": sizeSqm,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,  # not sent by the app yet so the preprocessor fills in the median
        "property_type": TYPE_NAMES.get(type, type),
        "ber": BER_SCORE.get(str(berRating).upper()),  # B2 becomes 11 like in data.py
        "latitude": latitude,
        "longitude": longitude,
    }])


# uses the trained model to predict what the house is worth
def predict_price(county, sizeSqm, bedrooms, type, berRating, bathrooms=None,
                  latitude=None, longitude=None):
    load_model()
    house = prepare_house(county, sizeSqm, bedrooms, type, berRating, bathrooms,
                          latitude, longitude)

    # prepare it the same way as the training data then predict
    prepared = pd.DataFrame(preprocessor.transform(house), columns=preprocessor.get_feature_names_out())
    return float(model.predict(prepared)[0])


# compares the asking price to the estimate and works out the ltv
def make_verdict(askingPrice, estimate, deposit):
    reasons = []

    # how much more or less the asking price is than the estimate eg 0.25 means 25% more
    gap = (askingPrice - estimate) / estimate

    if gap > FAIR_RANGE:
        verdict = "OVERPRICED"
        reasons.append(f"asking price is {gap:.0%} above the estimate of €{estimate:,.0f}")
    elif gap < -FAIR_RANGE:
        verdict = "UNDERPRICED"
        reasons.append(f"asking price is {-gap:.0%} below the estimate of €{estimate:,.0f}")
    else:
        verdict = "FAIR"
        reasons.append(f"asking price is within {FAIR_RANGE:.0%} of the estimate of €{estimate:,.0f}")

    # banks lend against whichever is lower the price or the valuation
    # same formula as docs/schema.md in the team repo
    loan = askingPrice - deposit
    ltv = loan / min(askingPrice, estimate) * 100
    if ltv <= MAX_LTV:
        reasons.append(f"loan is {ltv:.1f}% of the property value limit is {MAX_LTV}%")
    else:
        reasons.append(f"loan is {ltv:.1f}% of the property value over the {MAX_LTV}% limit")

    reasons.append(f"the estimate can be about {FAIR_RANGE:.0%} off so treat it as a guide")

    return {
        "askingPrice": round(askingPrice),
        "mlValuation": round(estimate),  # same name as the schema
        "gapPct": round(gap * 100, 1),
        "verdict": verdict,
        "ltv": round(ltv, 1),
        "ltvOk": ltv <= MAX_LTV,
        "reasons": reasons,
    }


# does both steps predict the price then compare it
def check_valuation(county, sizeSqm, bedrooms, type, berRating, askingPrice, deposit,
                    bathrooms=None, latitude=None, longitude=None):
    estimate = predict_price(county, sizeSqm, bedrooms, type, berRating, bathrooms,
                             latitude, longitude)
    return make_verdict(askingPrice, estimate, deposit)


# try it out  python valuation.py
if __name__ == "__main__":
    # the same fields the app sends
    result = check_valuation(county="Cork", sizeSqm=110, bedrooms=3, type="Semi-D",
                             berRating="C1", askingPrice=420000, deposit=42000)
    print(result["verdict"])
    for reason in result["reasons"]:
        print(" ", reason)