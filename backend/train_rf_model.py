import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL  # important for Neon
)



# 🔹 Fetch full dataset
def fetch_all_sales():
    print("fetching data...")
    query = """
    SELECT *
    FROM sales_history
    ORDER BY sale_date
    """
    return pd.read_sql(query, engine)


# 🔹 Feature Engineering (same as before)
def prepare_features(df):
    print("preparing features...")
    df = df.copy()

    df.rename(columns={"quantity_sold": "demand"}, inplace=True)

    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Lag features
    df["lag_1"] = df["demand"].shift(1)
    df["lag_7"] = df["demand"].shift(7)

    # Rolling
    df["rolling_mean_7"] = df["demand"].rolling(7).mean()

    # Date features
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    df = df.dropna().reset_index(drop=True)

    return df


# 🔹 MAIN TRAINING FUNCTION
def train_rf():

    df = fetch_all_sales()

    df = prepare_features(df)
    print("training the rf model...")

    feature_cols = [
        "lag_1",
        "lag_7",
        "rolling_mean_7",
        "day_of_week",
        "month",
        "is_weekend"
    ]

    # 🔥 Ensure numeric
    df[feature_cols] = (
        df[feature_cols]
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    X = df[feature_cols]
    y = df["demand"]

    # 🔹 Train-test split (IMPORTANT)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    # 🔥 Random Forest Model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # 🔹 Evaluation
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = root_mean_squared_error(y_test, preds)

    print("Random Forest Performance:")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")

    # 🔹 Save model
    joblib.dump(model, "rf_model.pkl")
    print("Model saved as rf_model.pkl")


if __name__ == "__main__":
    train_rf()