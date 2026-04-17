import pandas as pd
import joblib
from database import engine

    


# Load trained model (trained separately)
MODEL_PATH = "services/forecaster_model.pkl"
model = joblib.load(MODEL_PATH)


# 🔹 Fetch data from DB
def fetch_sales_data(product_id, warehouse_id):
    query = """
    SELECT *
    FROM sales_history
    WHERE product_id = %s
      AND warehouse_id = %s
    ORDER BY sale_date
    """
    df = pd.read_sql(query, engine, params=(product_id, warehouse_id))
    return df


# 🔹 Feature Engineering (VERY IMPORTANT)
def prepare_features(df):
    df = df.copy()

    # Rename for consistency
    df.rename(columns={"quantity_sold": "demand"}, inplace=True)

    # Lag features
    df["lag_1"] = df["demand"].shift(1)
    df["lag_7"] = df["demand"].shift(7)

    # Rolling mean
    df["rolling_mean_7"] = df["demand"].rolling(window=7).mean()

    # Date features
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Drop NaN rows (due to lagging)
    df.dropna(inplace=True)

    return df


# 🔹 Forecast Function (MAIN)
def forecast_demand(product_id, warehouse_id, steps):

    # df = fetch_sales_data(product_id, warehouse_id)

    # if df.empty or len(df) < 10:
    #     # fallback (important for MVP)
    #     return df["quantity_sold"].mean() if not df.empty else 0

    # df = prepare_features(df)

    # # Take latest row for prediction

    # feature_cols = [
    #     "lag_1",
    #     "lag_7",
    #     "rolling_mean_7",
    #     "day_of_week",
    #     "month",
    #     "is_weekend"
    # ]

    # print(df.head().dtypes)

    # # 🔥 Convert to numeric
    # df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors='coerce')
    # df[feature_cols] = df[feature_cols].fillna(0)
    # latest = df.iloc[-1]

    # X = latest[feature_cols].to_frame().T


    # # enforce correct dtypes
    # X["lag_1"] = X["lag_1"].astype(float)
    # X["lag_7"] = X["lag_7"].astype(float)
    # X["rolling_mean_7"] = X["rolling_mean_7"].astype(float)
    # X["day_of_week"] = X["day_of_week"].astype(int)
    # X["month"] = X["month"].astype(int)
    # X["is_weekend"] = X["is_weekend"].astype(int)
    
    # prediction = model.predict(X)[0]

    # # Safety: avoid negative predictions
    # return max(0, float(prediction))
        # 🔹 Fetch & prepare data
    df = fetch_sales_data(product_id, warehouse_id)

    if df.empty or len(df) < 10:
        return {
            "dates": [],
            "actual": [],
            "forecast": []
        }

    df = prepare_features(df)

    feature_cols = [
        "lag_1",
        "lag_7",
        "rolling_mean_7",
        "day_of_week",
        "month",
        "is_weekend"
    ]

    # 🔹 Ensure numeric types
    df[feature_cols] = (
        df[feature_cols]
        .astype(str)
        .apply(lambda col: col.str.strip())
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    # 🔥 RECURSIVE FORECASTING (future)
    history = df.copy()
    forecast_values = []
    forecast_dates = []

    for _ in range(steps):

        last_row = history.iloc[-1]

        # Prepare input
        X = last_row[feature_cols].to_frame().T

        X = inforce_dtypes(X)

        pred = float(model.predict(X)[0])
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

        # Append to history
        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)

    return {
        "dates": forecast_dates,
        "values": [float(v) for v in forecast_values]
    }

def inforce_dtypes(X: pd.DataFrame):
    # enforce correct dtypes
    X["lag_1"] = X["lag_1"].astype(float)
    X["lag_7"] = X["lag_7"].astype(float)
    X["rolling_mean_7"] = X["rolling_mean_7"].astype(float)
    X["day_of_week"] = X["day_of_week"].astype(int)
    X["month"] = X["month"].astype(int)
    X["is_weekend"] = X["is_weekend"].astype(int)
    return X