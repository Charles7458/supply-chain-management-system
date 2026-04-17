from fastapi import APIRouter, Depends
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from services.forecasting import fetch_sales_data
from services.forecasting import prepare_features
from services.forecasting import inforce_dtypes
from services.rf_predictor import forecast_demand_rf
from services.forecasting import forecast_demand as forecast_demand_lgb

router = APIRouter(prefix="/forecast", tags=["Forecast"])

# 🔹 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/demand-trend")
def get_demand_trend(product_id: int, warehouse_id: int, db: Session = Depends(get_db)):

    query = """
    SELECT sale_date, quantity_sold
    FROM sales_history
    WHERE product_id = :product_id
    AND warehouse_id = :warehouse_id
    ORDER BY sale_date
    """

    result = db.execute(text(query), {
        "product_id": product_id,
        "warehouse_id": warehouse_id
    }).mappings().all()

    return result

@router.get("/comparison")
def forecast_comparison(
    product_id: int,
    warehouse_id: int, 
    steps: int = 30,
    model: str = "lgb"
):

    # 🔹 Fetch & prepare data
    df = fetch_sales_data(product_id, warehouse_id)

    df = prepare_features(df)

    if df.empty or len(df) < 10:
        return {
            "dates": [],
            "actual": [],
            "forecast": []
        }

    if(model == "rf"):
        forecast = forecast_demand_rf(product_id, warehouse_id, steps)
    
    else:
        forecast = forecast_demand_lgb(product_id, warehouse_id, steps)

    # 🔹 ACTUAL DATA (past)
    actual_dates = df["sale_date"].astype(str).tolist()
    actual_values = df["demand"].astype(int).tolist()


    return {
        "actual": {
            "dates": actual_dates,
            "values": actual_values
        },
        "forecast": forecast
    }

@router.get("/compare-all")
def compare_all_models(product_id: int, warehouse_id: int):

    from services.rf_predictor import forecast_demand_rf
    from services.forecasting import fetch_sales_data, prepare_features
    import joblib

    lgb_model = joblib.load("services/forecaster_model.pkl")

    df = fetch_sales_data(product_id, warehouse_id)

    if df.empty or len(df) < 10:
        return {}

    df = prepare_features(df)

    feature_cols = [
        "lag_1", "lag_7", "rolling_mean_7",
        "day_of_week", "month", "is_weekend"
    ]

    df[feature_cols] = (
        df[feature_cols]
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    # 🔹 ACTUAL
    actual_dates = df["sale_date"].astype(str).tolist()
    actual_values = df["demand"].astype(int).tolist()

    # 🔹 RF Forecast
    rf_result = forecast_demand_rf(product_id, warehouse_id)

    # 🔹 LGBM Forecast (recursive like RF)
    history = df.copy()
    lgb_forecast = []
    lgb_dates = []

    steps = 30

    for _ in range(steps):

        last_row = history.iloc[-1]
        X = last_row[feature_cols].to_frame().T
        X = inforce_dtypes(X)
        pred = float(lgb_model.predict(X)[0])
        pred = max(0, pred)

        lgb_forecast.append(pred)

        new_row = last_row.copy()
        new_row["demand"] = pred

        new_row["lag_1"] = pred
        new_row["lag_7"] = history.iloc[-7]["demand"] if len(history) >= 7 else pred
        new_row["rolling_mean_7"] = history["demand"].tail(7).mean()

        next_date = pd.to_datetime(last_row["sale_date"]) + pd.Timedelta(days=1)

        new_row["sale_date"] = next_date
        new_row["day_of_week"] = next_date.dayofweek
        new_row["month"] = next_date.month
        new_row["is_weekend"] = int(next_date.dayofweek in [5, 6])

        lgb_dates.append(str(next_date.date()))

        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)

    return {
        "actual": {
            "dates": actual_dates,
            "values": actual_values
        },
        "rf": rf_result,
        "lgb": {
            "dates": lgb_dates,
            "values": [float(v) for v in lgb_forecast]
        }
    }