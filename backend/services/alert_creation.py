
def generate_alert(product_id, warehouse_id, result, stock_level):

    if result["status"] == "REORDER":
        alert_type = "REORDER_REQUIRED"
        message = f"""
Reorder required: Product {product_id} at Warehouse {warehouse_id}
has stock {stock_level}, below reorder point {result['reorder_point']}.
Recommended order: {result['recommended_order_qty']}.
"""

    elif stock_level < result["safety_stock"]:
        alert_type = "CRITICAL_LOW"
        message = f"""
Critical stock level: Product {product_id} at Warehouse {warehouse_id}
is below safety stock ({result['safety_stock']}).
"""

    elif stock_level > result["avg_demand"] * 60:
        alert_type = "OVERSTOCK"
        message = f"""
Overstock alert: Product {product_id} at Warehouse {warehouse_id}
has excess inventory ({stock_level} units).
"""

    else:
        return None

    return {
        "alert_type": alert_type,
        "alert_message": message.strip()
    }