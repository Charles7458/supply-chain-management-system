from fastapi import APIRouter, Depends, Query
from database import SessionLocal
from services.forecasting import forecast_demand
from services.optimizer import compute_inventory_policy
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter()

# 🔹 DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# 📦 Inventory API
@router.get("/")
def get_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    sort_by: str = "product_name",
    order: str = "asc",
    search: str = None,
    warehouse_id: int = None,
    status: str = None,
    db: Session = Depends(get_db)
):


    allowed_sort_columns = {
        "product_name": "p.product_name",
        "warehouse_name": "w.warehouse_name",
        "stock_level": "i.stock_level",
        "reserved_stock": "i.reserved_stock"
    }

    sort_column = allowed_sort_columns.get(sort_by, "p.product_name")
    order = "DESC" if order.lower() == "desc" else "ASC"

    offset = (page - 1) * limit

    base_query = """
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    JOIN warehouses w ON i.warehouse_id = w.warehouse_id
    LEFT JOIN inventory_policies ip 
        ON i.product_id = ip.product_id 
        AND i.warehouse_id = ip.warehouse_id
    WHERE 1=1
    """

    params = {
        "limit": limit,
        "offset": offset
    }

    if search:
        base_query += """
        AND (
            LOWER(p.product_name) LIKE LOWER(:search)
            OR LOWER(w.warehouse_name) LIKE LOWER(:search)
        )
        """
        params["search"] = f"%{search}%"

    if warehouse_id:
        base_query += " AND i.warehouse_id = :warehouse_id"
        params["warehouse_id"] = warehouse_id

    count_query = "SELECT COUNT(*) " + base_query
    total = db.execute(text(count_query), params).scalar()

    query = f"""
    SELECT 
        p.product_id,
        p.product_name,
        w.warehouse_id,
        w.warehouse_name,
        i.stock_level,
        i.reserved_stock,
        ip.safety_stock,
        ip.reorder_point
    {base_query}
    ORDER BY {sort_column} {order}
    LIMIT :limit OFFSET :offset
    """

    result = db.execute(text(query), params).mappings().all()

    response = []

    for row in result:

        available = row["stock_level"] - row["reserved_stock"]

        safety = row["safety_stock"]
        reorder = row["reorder_point"]

        # 🔥 STEP 1: If policy missing → compute & store
        if safety is None or reorder is None:

            policy = compute_inventory_policy(
                product_id=row["product_id"],
                warehouse_id=row["warehouse_id"]
            )

            safety = policy["safety_stock"]
            reorder = policy["reorder_point"]

            # 🔥 Insert into DB (UPSERT)
            db.execute(text("""
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
            """), {
                "product_id": row["product_id"],
                "warehouse_id": row["warehouse_id"],
                "safety_stock": safety,
                "reorder_point": reorder,
                "order_qty": policy["recommended_order_qty"]
            })

            db.commit()

        # 🔥 STEP 2: Compute status using REAL policy
        if available <= 0:
            computed_status = "CRITICAL"

        elif available <= safety:
            computed_status = "CRITICAL"

        elif available <= reorder:
            computed_status = "REORDER"

        else:
            computed_status = "NORMAL"

        if status and computed_status != status:
            continue

        response.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "warehouse_id": row["warehouse_id"],
            "warehouse_name": row["warehouse_name"],
            "stock_level": row["stock_level"],
            "reserved_stock": row["reserved_stock"],
            "available_stock": available,
            "safety_stock": safety,
            "reorder_point": reorder,
            "status": computed_status
        })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": response
    }

@router.get("/{product_id}/{warehouse_id}")
def get_inventory_specific(
    product_id: int = None,
    warehouse_id: int = None,
    db: Session = Depends(get_db)
):

    query = """
    SELECT 
        p.product_id,
        p.product_name,
        w.warehouse_id,
        w.warehouse_name,
        i.stock_level,
        i.reserved_stock,
        COALESCE(ip.safety_stock, 0) AS safety_stock,
        COALESCE(ip.reorder_point, 0) AS reorder_point
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    JOIN warehouses w ON i.warehouse_id = w.warehouse_id
    LEFT JOIN inventory_policies ip 
        ON i.product_id = ip.product_id 
        AND i.warehouse_id = ip.warehouse_id
    
    """

    params = {}

    if product_id:
        query += " AND i.product_id = :product_id"
        params["product_id"] = product_id

    if warehouse_id:
        query += " AND i.warehouse_id = :warehouse_id"
        params["warehouse_id"] = warehouse_id

    result = db.execute(text(query), params).mappings().all()

    response = []

    for row in result:
        available = row["stock_level"] - row["reserved_stock"]

        # 🔥 Status Logic
        if available <= row["safety_stock"]:
            status = "CRITICAL"
        elif available <= row["reorder_point"]:
            status = "REORDER"
        else:
            status = "NORMAL"

        response.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "warehouse_id": row["warehouse_id"],
            "warehouse_name": row["warehouse_name"],
            "stock_level": row["stock_level"],
            "reserved_stock": row["reserved_stock"],
            "available_stock": available,
            "status": status
        })

    return response

@router.get("/optimize/{product_id}/{warehouse_id}")
def optimize(db:Session = Depends(get_db)):
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