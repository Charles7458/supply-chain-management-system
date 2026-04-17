from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from database import SessionLocal
import pandas as pd
from services.forecasting import forecast_demand, fetch_sales_data, prepare_features

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# 🔹 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 📈 Demand Trend API
@router.get("/demand-trend")
def get_demand_trend(
    product_id: int,
    warehouse_id: int,
    days: Optional[int] = Query(30, description="Number of days to fetch"),
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT 
            sale_date::date AS date,
            SUM(quantity_sold) AS demand
        FROM sales_history
        WHERE product_id = :pid
          AND warehouse_id = :wid
        GROUP BY sale_date
        ORDER BY sale_date DESC
        LIMIT :days
    """)

    result = db.execute(query, {
        "pid": product_id,
        "wid": warehouse_id,
        "days": days
    })

    data = [dict(row._mapping) for row in result]

    # 🔄 reverse to ascending order for charts
    data.reverse()

    return data


# 📊 Forecast vs Actual API
@router.get("/forecast-comparison")
def forecast_comparison(
    product_id: int,
    warehouse_id: int,
    days: Optional[int] = Query(30, description="Number of days"),
    db: Session = Depends(get_db)
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
    
    forecast = forecast_demand(product_id, warehouse_id, days)

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

# 🚨 Alerts List API
@router.get("/alerts")
def get_alerts(
    limit: int = Query(10, description="Number of alerts to return"),
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    db: Session = Depends(get_db)
):

    query = """
        SELECT 
            alert_id,
            product_id,
            warehouse_id,
            alert_type,
            alert_message,
            created_at
        FROM alerts
        WHERE 1=1
    """

    params = {}

    # 🔹 Optional filters
    if product_id:
        query += " AND product_id = :pid"
        params["pid"] = product_id

    if warehouse_id:
        query += " AND warehouse_id = :wid"
        params["wid"] = warehouse_id

    if alert_type:
        query += " AND alert_type = :atype"
        params["atype"] = alert_type

    # 🔹 Ordering + limit
    query += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)

    alerts = [
        {
            "alert_id": row.alert_id,
            "product_id": row.product_id,
            "warehouse_id": row.warehouse_id,
            "alert_type": row.alert_type,
            "alert_message": row.alert_message,
            "created_at": row.created_at.isoformat()
        }
        for row in result
    ]

    return alerts

# 📊 Summary API
@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):

    # 🔹 Basic counts
    total_products = db.execute(
        text("SELECT COUNT(*) FROM products")
    ).scalar()

    total_warehouses = db.execute(
        text("SELECT COUNT(*) FROM warehouses")
    ).scalar()

    total_alerts = db.execute(
        text("SELECT COUNT(*) FROM alerts")
    ).scalar()

    # 🔹 Alert breakdown
    critical_alerts = db.execute(text("""
        SELECT COUNT(*) FROM alerts
        WHERE alert_type = 'CRITICAL'
    """)).scalar()

    reorder_alerts = db.execute(text("""
        SELECT COUNT(*) FROM alerts
        WHERE alert_type = 'REORDER'
    """)).scalar()

    # 🔹 Inventory health (from policies)
    normal_items = db.execute(text("""
        SELECT COUNT(*) FROM inventory_policies
        WHERE status = 'NORMAL'
    """)).scalar()

    return {
        "total_products": total_products or 0,
        "total_warehouses": total_warehouses or 0,
        "total_alerts": total_alerts or 0,
        "critical_alerts": critical_alerts or 0,
        "reorder_alerts": reorder_alerts or 0,
        "normal_items": normal_items or 0
    }