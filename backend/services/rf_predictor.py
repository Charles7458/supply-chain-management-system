# services/rf_predictor.py

import pandas as pd
import joblib
from database import engine
from services.forecasting import inforce_dtypes

# 🔹 Load model once
MODEL_PATH = "services/rf_model.pkl"
rf_model = joblib.load(MODEL_PATH)


# 🔹 Fetch data
def fetch_sales_data(product_id, warehouse_id):
    query = """
    SELECT *
    FROM sales_history
    WHERE product_id = %s
      AND warehouse_id = %s
    ORDER BY sale_date
    """
    return pd.read_sql(query, engine, params=(product_id, warehouse_id))


# 🔹 Feature Engineering
def prepare_features(df):
    df = df.copy()

    df.rename(columns={"quantity_sold": "demand"}, inplace=True)

    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Lag features
    df["lag_1"] = df["demand"].shift(1)
    df["lag_7"] = df["demand"].shift(7)

    # Rolling mean
    df["rolling_mean_7"] = df["demand"].rolling(7).mean()

    # Date features
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    df = df.dropna().reset_index(drop=True)

    return df


# 🔥 MAIN FORECAST FUNCTION (Recursive)
def forecast_demand_rf(product_id, warehouse_id, steps=30):

    df = fetch_sales_data(product_id, warehouse_id)

    if df.empty or len(df) < 10:
        return []

    df = prepare_features(df)

    feature_cols = [
        "lag_1",
        "lag_7",
        "rolling_mean_7",
        "day_of_week",
        "month",
        "is_weekend"
    ]

    # 🔹 Ensure numeric
    df[feature_cols] = (
        df[feature_cols]
        .astype(str)
        .apply(lambda col: col.str.strip())
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    history = df.copy()

    forecast_values = []
    forecast_dates = []

    for _ in range(steps):

        last_row = history.iloc[-1]

        X = last_row[feature_cols].to_frame().T

        X = inforce_dtypes(X)

        pred = float(rf_model.predict(X)[0])

        # Optional safety
        pred = max(0, pred)

        forecast_values.append(pred)

        # 🔥 Create next row
        new_row = last_row.copy()
        new_row["demand"] = pred

        # Update lag features
        new_row["lag_1"] = pred

        if len(history) >= 7:
            new_row["lag_7"] = history.iloc[-7]["demand"]
        else:
            new_row["lag_7"] = pred

        new_row["rolling_mean_7"] = history["demand"].tail(7).mean()

        # Update date
        next_date = pd.to_datetime(last_row["sale_date"]) + pd.Timedelta(days=1)
        new_row["sale_date"] = next_date

        new_row["day_of_week"] = next_date.dayofweek
        new_row["month"] = next_date.month
        new_row["is_weekend"] = int(next_date.dayofweek in [5, 6])

        forecast_dates.append(str(next_date.date()))

        # Append
        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)

    return {
        "dates": forecast_dates,
        "values": [float(v) for v in forecast_values]
    }