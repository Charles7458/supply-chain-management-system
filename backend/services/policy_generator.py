from sqlalchemy.orm import Session
from sqlalchemy import text
from services.forecasting import forecast_demand


def generate_policies(db: Session):

    # 🔹 Get all product-warehouse combinations
    query = """
    SELECT product_id, warehouse_id
    FROM inventory
    """
    rows = db.execute(text(query)).mappings().all()

    for row in rows:
        product_id = int(row["product_id"])
        warehouse_id = int(row["warehouse_id"])

        # 🔥 ML Forecast
        avg_demand = forecast_demand(product_id, warehouse_id)

        # ⚙️ Business constants (can later move to config)
        lead_time = 5
        safety_days = 3
        order_cycle_days = 15

        # 🔹 Calculations
        safety_stock = int(avg_demand * safety_days)
        reorder_point = int(avg_demand * lead_time + safety_stock)
        order_qty = int(avg_demand * order_cycle_days)

        

        # 🔥 Upsert into DB
        upsert_query = """
        INSERT INTO inventory_policies (
            product_id,
            warehouse_id,
            safety_stock,
            reorder_point,
            recommended_order_qty,
            status
        )
        VALUES (
            :product_id,
            :warehouse_id,
            :safety_stock,
            :reorder_point,
            :order_qty,
            'ACTIVE'
        )
        ON CONFLICT (product_id, warehouse_id)
        DO UPDATE SET
            safety_stock = EXCLUDED.safety_stock,
            reorder_point = EXCLUDED.reorder_point,
            recommended_order_qty = EXCLUDED.recommended_order_qty,
            calculated_at = CURRENT_TIMESTAMP
        """

        db.execute(text(upsert_query), {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "order_qty": order_qty
        })

    db.commit()