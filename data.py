# cleans the daft.ie dataset so it can be used to train the valuation model

# saves the results in a folder called data/processed

import os

import joblib
import kagglehub as kh
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# same split settings used again by the training script
TEST_SIZE = 0.2  # 20% of the data is kept back for testing
RANDOM_STATE = 7  # makes the split the same every time its run

# have to get rid of counties in the north of Ireland because they can be listed in pounds and it causes issues
IRISH_COUNTIES = [
    "Carlow", "Cavan", "Clare", "Cork", "Donegal", "Dublin", "Galway", "Kerry",
    "Kildare", "Kilkenny", "Laois", "Leitrim", "Limerick", "Longford", "Louth",
    "Mayo", "Meath", "Monaghan", "Offaly", "Roscommon", "Sligo", "Tipperary",
    "Waterford", "Westmeath", "Wexford", "Wicklow",
]

# BER grades turned into a score so the model knows A1 is better than G basically just giving the model a numerical meteric to work off of
BER_SCORE = {
    "G": 1, "F": 2, "E2": 3, "E1": 4, "D2": 5, "D1": 6, "C3": 7, "C2": 8,
    "C1": 9, "B3": 10, "B2": 11, "B1": 12, "A3": 13, "A2": 14, "A1": 15,
}

NUMBER_COLUMNS = ["floor_area", "bedrooms", "bathrooms", "ber", "latitude", "longitude"]
TEXT_COLUMNS = ["county", "property_type"]


# fills in blanks and encodes the text columns and scales the number columns
def build_preprocessor():
    numbers = Pipeline([
        ("fill_blanks", SimpleImputer(strategy="median")),  # blank goes to middle value
        ("scale", StandardScaler()),  # puts all numbers on the same scale
    ])
    text = Pipeline([
        ("fill_blanks", SimpleImputer(strategy="most_frequent")),  # blank -> most common
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),  # one 0/1 column per value
    ])
    return ColumnTransformer([
        ("numbers", numbers, NUMBER_COLUMNS),
        ("text", text, TEXT_COLUMNS),
    ])


# this part only runs when you run this file, not when the training script imports
# build_preprocessor from it
if __name__ == "__main__":
    #load the data
    folder = kh.dataset_download("adnankhalid007/ireland-house-properties-dataset-2024")
    df = pd.read_csv(f"{folder}/daft_housing_data.csv")
    print("Loaded:", len(df))

    #  remove duplicates, copies, and the same address listed twice at the same price
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["Title", "Price"])
    print("After removing duplicates:", len(df))

    # keep only the columns the model needs
    df = df.rename(columns={
        "Price": "price",
        "County": "county",
        "Floor Area (m2)": "floor_area",
        "Number of Bedrooms": "bedrooms",
        "Number of Bathrooms": "bathrooms",
        "Property Type": "property_type",
        "BER Rating": "ber",
        "Latitude": "latitude",
        "Longitude": "longitude",
    })
    df = df[["price", "county", "floor_area", "bedrooms", "bathrooms", "property_type", "ber", "latitude", "longitude"]]

    # any price that isn't a plain number becomes blank, then those rows are dropped.
    # This removes "Price on Application", "From" prices, "AMV", and the pound price
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    print("After removing rows with no usable price:", len(df))

    # drop land and new developments and replace "House" with "Detached"
    df = df[~df["property_type"].isin(["Site", "Houses", "New Homes", "Property"])]
    df = df.dropna(subset=["property_type"])
    df["property_type"] = df["property_type"].replace("House", "Detached")
    print("After removing sites and developments:", len(df))

    # keep only the 26 counties drops blanks and north of Ireland
    df = df[df["county"].isin(IRISH_COUNTIES)]
    print("After removing rows outside the 26 counties:", len(df))

    # remove stray commas like "2," then make it a number like just "2"
    df["bedrooms"] = pd.to_numeric(df["bedrooms"].str.replace(",", ""))

    # values that really mean not filled in yet just become blank
    df.loc[(df["floor_area"] < 20) | (df["floor_area"] > 1000), "floor_area"] = np.nan
    df.loc[(df["bedrooms"] == 0) & (df["property_type"] != "Studio"), "bedrooms"] = np.nan
    df.loc[df["bathrooms"] == 0, "bathrooms"] = np.nan

    # trnaslates grade to score Anything else  like blank, SI_666, BER_PENDING becomes blank
    df["ber"] = df["ber"].map(BER_SCORE)

    # deals with price outliers using the IQR rule on log(price) log is used because a few
    # very expensive homes stretch the prices out and the log scale they are spread evenly
    log_price = np.log(df["price"])
    q1 = log_price.quantile(0.25)
    q3 = log_price.quantile(0.75)
    iqr = q3 - q1
    df = df[(log_price >= q1 - 1.5 * iqr) & (log_price <= q3 + 1.5 * iqr)]
    print("After removing price outliers:", len(df))

    print("\nBlanks left in each column (filled in at step 12):")
    print(df.isna().sum())

    # split into train and test before filling blanks and scaling so the test data has no influence on the training data
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/cleaned_full.csv", index=False)

    X = df.drop(columns="price")
    y = df["price"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE)

    # fill blanks and encode and scale and fit_transform learns the medians and scales from the training data and transform applies those same values to the test data
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(X_train)
    X_test = preprocessor.transform(X_test)

    # save everything
    columns = preprocessor.get_feature_names_out()
    train = pd.DataFrame(X_train, columns=columns)
    train["price"] = y_train.values
    test = pd.DataFrame(X_test, columns=columns)
    test["price"] = y_test.values

    train.to_csv("data/processed/train.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)
    joblib.dump(preprocessor, "data/processed/preprocessor.joblib")

    print(f"\nDone. Train: {len(train)} rows, Test: {len(test)} rows")