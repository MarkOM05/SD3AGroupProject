# tests for the valuation agent mostly the borderline cases
# these dont load the big model file so they run fast anywhere
# run with pytest -v

from valuation import COUNTY_CENTRES, make_verdict, prepare_house


def test_same_as_estimate_is_fair():
    assert make_verdict(300000, 300000, 30000)["verdict"] == "FAIR"


# overpriced boundary 20% above the estimate

def test_exactly_20_percent_above_is_fair():
    assert make_verdict(360000, 300000, 36000)["verdict"] == "FAIR"


def test_just_over_20_percent_above_is_overpriced():
    assert make_verdict(361000, 300000, 36100)["verdict"] == "OVERPRICED"


# underpriced boundary 20% below the estimate

def test_exactly_20_percent_below_is_fair():
    assert make_verdict(240000, 300000, 24000)["verdict"] == "FAIR"


def test_just_under_20_percent_below_is_underpriced():
    assert make_verdict(239000, 300000, 23900)["verdict"] == "UNDERPRICED"


# ltv tests limit is 90%

def test_ltv_uses_the_lower_of_price_and_estimate():
    # 270k loan on a 300k asking price but its only worth 280k so ltv is 270/280
    result = make_verdict(300000, 280000, 30000)
    assert result["ltv"] == 96.4
    assert result["ltvOk"] is False


def test_10_percent_deposit_on_fair_price_is_ok():
    result = make_verdict(300000, 300000, 30000)
    assert result["ltv"] == 90.0
    assert result["ltvOk"] is True


# turning the apps fields into what the model expects

def test_no_location_uses_the_middle_of_the_county():
    house = prepare_house("Cork", 110, 3, "Semi-D", "C1")
    assert house["latitude"][0] == COUNTY_CENTRES["Cork"][0]
    assert house["longitude"][0] == COUNTY_CENTRES["Cork"][1]


def test_exact_location_is_used_when_given():
    house = prepare_house("Cork", 110, 3, "Semi-D", "C1", latitude=51.9, longitude=-8.47)
    assert house["latitude"][0] == 51.9


def test_terraced_from_the_app_becomes_terrace():
    assert prepare_house("Dublin", 90, 3, "Terraced", "C1")["property_type"][0] == "Terrace"


def test_ber_grade_becomes_a_score():
    assert prepare_house("Dublin", 90, 3, "Semi-D", "b2")["ber"][0] == 11


def test_lowercase_county_still_works():
    assert prepare_house("dublin", 90, 3, "Semi-D", "B2")["county"][0] == "Dublin"


def test_all_26_counties_have_a_centre():
    assert len(COUNTY_CENTRES) == 26