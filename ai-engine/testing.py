import pandas as pd
import kagglehub as kh

# setting this so I can see all the wider colums and it dosent get cut off
pd.set_option("display.width", 140)

# setting this so I can see all the columns and also dosent get cut off during testing
pd.set_option("display.max_columns", 20)


# formats a number with commas and no decimal places 35000000.0 goes to 35,000,000
def format_number(v):
    return f"{v:,.0f}"


# sets folder path in variable for reusue
folder = kh.dataset_download("adnankhalid007/ireland-house-properties-dataset-2024")
# sets path to actual csv inside folder
csv_path = f"{folder}/daft_housing_data.csv"

df = pd.read_csv(csv_path)


print("\n--- 1. Overview ---")
#print length amount of rows and columns the ":," puts commas in the thousands
print(f"{len(df):,} rows, {df.shape[1]} columns\n")

#small summary table on how much data is missing and the percentage
overview = pd.DataFrame({"type": df.dtypes.astype(str),"missing": df.isna().sum(), "missing_%": (df.isna().mean() * 100).round(1),})
# turns the type names into plain text so it prints better
print(overview)


print("\n--- 2. Price ---")
price_num = pd.to_numeric(df["Price"], errors = "coerce")
#converts the price column to numbers errors is anything that cant be  converted like price on application becomes na instead of crashing

# finds prices that failed to convert but werent blank to begin with
not_numeric = df.loc[price_num.isna() & df["Price"].notna(), "Price"]

# replaces every digit with # so "From 575000" and "From 460000" count as one pattern
print(not_numeric.str.replace(r"\d", "#", regex=True).value_counts().head(10))

# summary of the prices that are numbers shows the very low and very high ones
print(price_num.describe().apply(format_number))


print("\n--- 3. Property type ---")
# shows anything thats not a single home
print(df["Property Type"].value_counts())


print("\n--- 4. Floor area ---")
# the max is far too big and the min is 0
print(df["Floor Area (m2)"].describe().apply(format_number))
print("Under 20 m²:", (df["Floor Area (m2)"] < 20).sum())


print("\n--- 5. Bedrooms and bathrooms ---")
# shows 0 bedrooms,and values with a stray comma like "2,"
print(df["Number of Bedrooms"].value_counts())
print("0 bathrooms:", (df["Number of Bathrooms"] == 0).sum())


print("\n--- 6. BER ---")
# shows blanks like SI_666 exempt and BER_PENDING which aren't real grades
print(df["BER Rating"].value_counts(dropna=False))


print("\n--- 7. County ---")
# shows blanks and North of ireland counties
print(df["County"].value_counts(dropna=False))


print("\n--- 8. Duplicates ---")
print("Exact duplicates:", df.duplicated().sum())
print("Same address and price:", df.duplicated(subset=["Title", "Price"]).sum())