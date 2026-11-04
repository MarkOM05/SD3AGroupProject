# Trains the valuation model on the cleaned data and saves the best one.
# Run clean_housing_data.py first, then:  python train_valuation_model.py
# Saves the model and results in a folder called models

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV

# 1. load the train and test data made by the cleaning script
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")

# X = the house details (inputs), y = the price (what we want to predict)
X_train = train.drop(columns="price")
y_train = train["price"]
X_test = test.drop(columns="price")
y_test = test["price"]


# works out the three scores for a model on the test data
def evaluate(model):
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)            # average error in euros
    rmse = np.sqrt(mean_squared_error(y_test, predictions))   # like MAE big misses count more
    r2 = r2_score(y_test, predictions)                        # 1.0 = perfect
    return mae, rmse, r2


# linear regression
baseline = LinearRegression()
baseline.fit(X_train, y_train)
print("Linear regression trained")

# random forest tuned with GridSearchCV
# It tries every combination of these settings 2 * 3 = 6 scoring each one with 5 fold cross validation on the training data and keeps the best
settings = {
    "n_estimators": [100, 300],     # how many trees
    "max_depth": [10, 20, None],    # how deep each tree can go None = no limit
}
search = GridSearchCV(RandomForestRegressor(random_state=27), settings, cv=5, n_jobs=-1) # for anyone running my code if it takes too long to run change cv which means cross validation to a lower number and itll run faster but be less accurate its an exponential increase in time complexity so itll save you a good bit of time jobs -1 also optimizes it to use all your cpu cores
search.fit(X_train, y_train)
forest = search.best_estimator_
print("Random forest trained Best settings:", search.best_params_)

# evaluate both on the test data, which neither model has seen
results = pd.DataFrame(
    [evaluate(baseline), evaluate(forest)],
    index=["Linear regression", "Random forest"],
    columns=["MAE €", "RMSE €", "R2"],
).round({"MAE €": 0, "RMSE €": 0, "R2": 3})
print("\nResults on the test data:")
print(results)

# save whichever model has the lower average error
os.makedirs("models", exist_ok=True)
if results.loc["Random forest", "MAE €"] < results.loc["Linear regression", "MAE €"]:
    best_name, best_model = "Random forest", forest
else:
    best_name, best_model = "Linear regression", baseline
joblib.dump(best_model, "models/valuation_model.joblib")
print(f"\nSaved {best_name} to models/valuation_model.joblib")

# save the results to a text file for the report
with open("models/results.txt", "w", encoding="utf-8") as f:
    f.write(f"Train rows: {len(train)}, Test rows: {len(test)}\n\n")
    f.write(results.to_string())
    f.write(f"\n\nRandom forest best settings: {search.best_params_}\n")
    f.write(f"Saved model: {best_name}\n")