import numpy as np
from services.forecasting import forecast_demand


# 🔹 CONFIG (you can tweak these)
LEAD_TIME_DAYS = 7          # how many days to restock
SERVICE_LEVEL = 1.65        # ~95% service level (Z-score)


def compute_inventory_policy(product_id: int, warehouse_id: int):
    """
    Computes:
    - avg_demand
    - safety_stock
    - reorder_point
    - recommended_order_qty
    """

    # 🔥 Step 1: Get forecast (future demand)
    forecast_values = forecast_demand(product_id, warehouse_id, 30)

    # Handle edge case
    if not forecast_values or len(forecast_values) == 0:
        return {
            "avg_demand": 0,
            "safety_stock": 0,
            "reorder_point": 0,
            "recommended_order_qty": 0
        }

    # 🔹 Step 2: Basic stats
    avg_demand = np.mean(forecast_values)
    demand_std = np.std(forecast_values)

    # 🔹 Step 3: Safety Stock
    safety_stock = SERVICE_LEVEL * demand_std * np.sqrt(LEAD_TIME_DAYS)

    # 🔹 Step 4: Reorder Point
    reorder_point = (avg_demand * LEAD_TIME_DAYS) + safety_stock

    # 🔹 Step 5: Recommended Order Quantity
    # Simple heuristic: order enough for next 30 days
    recommended_order_qty = avg_demand * 30

    # 🔹 Clean values (important)
    safety_stock = int(round(safety_stock))
    reorder_point = int(round(reorder_point))
    recommended_order_qty = int(round(recommended_order_qty))

    return {
        "avg_demand": float(avg_demand),
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "recommended_order_qty": recommended_order_qty,
        "status": "CALCULATED"
    }