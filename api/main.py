import os
import uuid
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    heroku_database_url = os.getenv("DATABASE_URL")
    if heroku_database_url:
        if heroku_database_url.startswith("postgres://"):
            DB_URL = heroku_database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif heroku_database_url.startswith("postgresql://"):
            DB_URL = heroku_database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        else:
            DB_URL = heroku_database_url

ACTIONS_API_KEY = os.getenv("ACTIONS_API_KEY")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")

if not DB_URL:
    raise RuntimeError("DB_URL is not set. Copy .env.example to .env and set DB_URL.")
if not ACTIONS_API_KEY:
    raise RuntimeError("ACTIONS_API_KEY is not set. Copy .env.example to .env and set ACTIONS_API_KEY.")

engine = create_engine(DB_URL, future=True)

app = FastAPI(
    title="Retail Demo GPT Actions API",
    version="1.0.0",
    description="Minimal unified retail demo API for store associate and merch planning workflows.",
    servers=[{"url": PUBLIC_BASE_URL}] if PUBLIC_BASE_URL else [],
)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def require_api_key(x_api_key: str | None = Security(api_key_header)) -> None:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key.")
    if x_api_key != ACTIONS_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")


def _fetch_one_or_404(query_text: str, params: dict, not_found_message: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(text(query_text), params).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message)
    return dict(row)


def _fetch_all(query_text: str, params: dict | None = None) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(text(query_text), params or {}).mappings().all()
    return [dict(row) for row in rows]


class HealthResponse(BaseModel):
    status: str


class ProductRecord(BaseModel):
    product_id: str
    style_id: str
    sku_id: str
    product_name: str
    category: str
    subcategory: str
    brand: str
    color: str
    size: str
    season: str
    msrp: float
    cost: float
    description: str
    image_url: str
    silhouette: str
    occasion: str
    material: str
    status: str


class ProductSearchResponse(BaseModel):
    products: list[ProductRecord]


class InventoryRecord(BaseModel):
    store_id: int
    store_name: str
    city: str
    state: str
    region: str
    store_type: str
    sku_id: str
    on_hand_qty: int
    reserved_qty: int
    available_qty: int
    in_transit_qty: int
    last_updated: datetime


class InventoryResponse(BaseModel):
    product_id: str
    inventory: list[InventoryRecord]


class RelatedProductRecord(BaseModel):
    source_product_id: str
    related_product_id: str
    relationship_type: str
    relationship_reason: str
    related_sku_id: str
    related_product_name: str
    related_category: str
    related_color: str
    related_size: str
    related_msrp: float
    related_image_url: str
    related_available_qty_in_origin_store: int | None
    related_total_available_qty: int


class ProductRelationshipsResponse(BaseModel):
    source_product_id: str
    relationships: list[RelatedProductRecord]


class OrderCreateItem(BaseModel):
    sku_id: str
    quantity: int = Field(..., ge=1, le=10)


class OrderCreateRequest(BaseModel):
    customer_id: str
    destination_store_id: int | None = None
    ship_to_city: str | None = None
    shipping_method: str = Field(default="standard", pattern=r"^(standard|expedited|overnight|store_pickup)$")
    fulfillment_store_id: int | None = None
    items: list[OrderCreateItem] = Field(..., min_length=1)


class OrderLineItemResponse(BaseModel):
    sku_id: str
    quantity: int
    unit_price: float
    line_total: float


class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    order_date: datetime
    order_status: str
    fulfillment_store_id: int
    fulfillment_store_name: str
    destination_store_id: int | None
    destination_store_name: str | None
    ship_to_city: str | None
    shipping_method: str
    estimated_delivery_days: int
    estimated_delivery_date: date
    total_amount: float
    line_items: list[OrderLineItemResponse]


class WeeklyPerformanceRecord(BaseModel):
    week_start_date: date
    store_id: int
    store_name: str
    category: str
    style_id: str
    units_sold: int
    net_sales: float
    gross_margin: float
    markdown_rate: float
    sell_through_pct: float
    weeks_of_supply: float


class WeeklyPerformanceResponse(BaseModel):
    performance: list[WeeklyPerformanceRecord]


class InventoryImbalanceRecord(BaseModel):
    sku_id: str
    style_id: str
    product_name: str
    category: str
    shortage_store_id: int
    shortage_store_name: str
    shortage_available_qty: int
    surplus_store_id: int
    surplus_store_name: str
    surplus_available_qty: int


class InventoryImbalanceResponse(BaseModel):
    imbalances: list[InventoryImbalanceRecord]


class PlanningRecommendationRecord(BaseModel):
    action_type: str
    priority: str
    style_id: str
    category: str
    source_store_id: int | None
    source_store_name: str | None
    target_store_id: int | None
    target_store_name: str | None
    recommended_units: int | None
    rationale: str


class PlanningRecommendationsResponse(BaseModel):
    recommendations: list[PlanningRecommendationRecord]


@app.get("/health", summary="Health check", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/products/search",
    dependencies=[Depends(require_api_key)],
    summary="Search products by name, category, or occasion",
    response_model=ProductSearchResponse,
)
def search_products(
    q: str | None = Query(default=None, min_length=2),
    category: str | None = None,
    occasion: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> ProductSearchResponse:
    rows = _fetch_all(
        """
        SELECT
            product_id, style_id, sku_id, product_name, category, subcategory, brand,
            color, size, season, msrp::float AS msrp, cost::float AS cost,
            description, image_url, silhouette, occasion, material, status
        FROM retail_demo.products
        WHERE (:q IS NULL OR product_name ILIKE :q_pattern OR style_id ILIKE :q_pattern OR sku_id ILIKE :q_pattern)
          AND (:category IS NULL OR category = :category)
          AND (:occasion IS NULL OR occasion = :occasion)
          AND status = 'active'
        ORDER BY category, product_name, color, size
        LIMIT :limit
        """,
        {
            "q": q,
            "q_pattern": f"%{q}%" if q else None,
            "category": category,
            "occasion": occasion,
            "limit": limit,
        },
    )
    return ProductSearchResponse(products=[ProductRecord(**row) for row in rows])


@app.get(
    "/products/{product_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get a product by product_id",
    response_model=ProductRecord,
)
def get_product(product_id: str) -> ProductRecord:
    row = _fetch_one_or_404(
        """
        SELECT
            product_id, style_id, sku_id, product_name, category, subcategory, brand,
            color, size, season, msrp::float AS msrp, cost::float AS cost,
            description, image_url, silhouette, occasion, material, status
        FROM retail_demo.products
        WHERE product_id = :product_id
        """,
        {"product_id": product_id},
        "Product not found.",
    )
    return ProductRecord(**row)


@app.get(
    "/inventory/products/{product_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get inventory across all stores for a product",
    response_model=InventoryResponse,
)
def get_inventory_for_product(product_id: str) -> InventoryResponse:
    product = _fetch_one_or_404(
        "SELECT product_id, sku_id FROM retail_demo.products WHERE product_id = :product_id",
        {"product_id": product_id},
        "Product not found.",
    )
    rows = _fetch_all(
        """
        SELECT
            s.store_id,
            s.store_name,
            s.city,
            s.state,
            s.region,
            s.store_type,
            i.sku_id,
            i.on_hand_qty,
            i.reserved_qty,
            i.available_qty,
            i.in_transit_qty,
            i.last_updated
        FROM retail_demo.inventory i
        JOIN retail_demo.stores s ON s.store_id = i.store_id
        WHERE i.sku_id = :sku_id
        ORDER BY i.available_qty DESC, i.in_transit_qty DESC
        """,
        {"sku_id": product["sku_id"]},
    )
    return InventoryResponse(product_id=product_id, inventory=[InventoryRecord(**row) for row in rows])


@app.get(
    "/inventory/products/{product_id}/stores/{store_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get inventory for a product at a specific store",
    response_model=InventoryResponse,
)
def get_inventory_for_product_store(product_id: str, store_id: int) -> InventoryResponse:
    product = _fetch_one_or_404(
        "SELECT product_id, sku_id FROM retail_demo.products WHERE product_id = :product_id",
        {"product_id": product_id},
        "Product not found.",
    )
    rows = _fetch_all(
        """
        SELECT
            s.store_id,
            s.store_name,
            s.city,
            s.state,
            s.region,
            s.store_type,
            i.sku_id,
            i.on_hand_qty,
            i.reserved_qty,
            i.available_qty,
            i.in_transit_qty,
            i.last_updated
        FROM retail_demo.inventory i
        JOIN retail_demo.stores s ON s.store_id = i.store_id
        WHERE i.sku_id = :sku_id
          AND i.store_id = :store_id
        """,
        {"sku_id": product["sku_id"], "store_id": store_id},
    )
    return InventoryResponse(product_id=product_id, inventory=[InventoryRecord(**row) for row in rows])


@app.get(
    "/products/{product_id}/relationships",
    dependencies=[Depends(require_api_key)],
    summary="Get alternative or complementary products with availability",
    response_model=ProductRelationshipsResponse,
)
def get_product_relationships(
    product_id: str,
    relationship_type: str | None = Query(default=None, pattern=r"^(alternative|complementary)$"),
    origin_store_id: int | None = None,
    limit: int = Query(default=10, ge=1, le=50),
) -> ProductRelationshipsResponse:
    _fetch_one_or_404(
        "SELECT product_id FROM retail_demo.products WHERE product_id = :product_id",
        {"product_id": product_id},
        "Product not found.",
    )
    rows = _fetch_all(
        """
        SELECT
            rel.source_product_id,
            rel.related_product_id,
            rel.relationship_type,
            rel.relationship_reason,
            p.sku_id AS related_sku_id,
            p.product_name AS related_product_name,
            p.category AS related_category,
            p.color AS related_color,
            p.size AS related_size,
            p.msrp::float AS related_msrp,
            p.image_url AS related_image_url,
            store_inv.available_qty AS related_available_qty_in_origin_store,
            COALESCE(total_inv.total_available_qty, 0) AS related_total_available_qty
        FROM retail_demo.product_relationships rel
        JOIN retail_demo.products p ON p.product_id = rel.related_product_id
        LEFT JOIN retail_demo.inventory store_inv
            ON store_inv.sku_id = p.sku_id
           AND (:origin_store_id IS NOT NULL AND store_inv.store_id = :origin_store_id)
        LEFT JOIN (
            SELECT sku_id, SUM(available_qty)::int AS total_available_qty
            FROM retail_demo.inventory
            GROUP BY sku_id
        ) total_inv ON total_inv.sku_id = p.sku_id
        WHERE rel.source_product_id = :product_id
          AND (:relationship_type IS NULL OR rel.relationship_type = :relationship_type)
        ORDER BY
            CASE rel.relationship_type WHEN 'alternative' THEN 0 ELSE 1 END,
            COALESCE(store_inv.available_qty, 0) DESC,
            COALESCE(total_inv.total_available_qty, 0) DESC
        LIMIT :limit
        """,
        {
            "product_id": product_id,
            "relationship_type": relationship_type,
            "origin_store_id": origin_store_id,
            "limit": limit,
        },
    )
    return ProductRelationshipsResponse(
        source_product_id=product_id,
        relationships=[RelatedProductRecord(**row) for row in rows],
    )


def _build_order_response(order_id: str) -> OrderResponse:
    header = _fetch_one_or_404(
        """
        SELECT
            o.order_id,
            o.customer_id,
            o.order_date,
            o.order_status,
            o.fulfillment_store_id,
            sf.store_name AS fulfillment_store_name,
            o.destination_store_id,
            sd.store_name AS destination_store_name,
            o.ship_to_city,
            o.shipping_method,
            o.estimated_delivery_days,
            o.estimated_delivery_date,
            COALESCE(SUM(li.quantity * li.unit_price), 0)::float AS total_amount
        FROM retail_demo.orders o
        JOIN retail_demo.stores sf ON sf.store_id = o.fulfillment_store_id
        LEFT JOIN retail_demo.stores sd ON sd.store_id = o.destination_store_id
        LEFT JOIN retail_demo.order_line_items li ON li.order_id = o.order_id
        WHERE o.order_id = :order_id
        GROUP BY
            o.order_id, o.customer_id, o.order_date, o.order_status,
            o.fulfillment_store_id, sf.store_name,
            o.destination_store_id, sd.store_name,
            o.ship_to_city, o.shipping_method, o.estimated_delivery_days, o.estimated_delivery_date
        """,
        {"order_id": order_id},
        "Order not found.",
    )
    items = _fetch_all(
        """
        SELECT
            sku_id,
            quantity,
            unit_price::float AS unit_price,
            (quantity * unit_price)::float AS line_total
        FROM retail_demo.order_line_items
        WHERE order_id = :order_id
        ORDER BY sku_id
        """,
        {"order_id": order_id},
    )
    return OrderResponse(
        **header,
        line_items=[OrderLineItemResponse(**row) for row in items],
    )


@app.post(
    "/orders",
    dependencies=[Depends(require_api_key)],
    summary="Place an order from another store and return ETA",
    response_model=OrderResponse,
)
def create_order(payload: OrderCreateRequest) -> OrderResponse:
    if payload.destination_store_id is None and payload.ship_to_city is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide destination_store_id or ship_to_city.",
        )

    with engine.begin() as conn:
        if payload.destination_store_id is not None:
            dest = conn.execute(
                text("SELECT store_id FROM retail_demo.stores WHERE store_id = :store_id"),
                {"store_id": payload.destination_store_id},
            ).mappings().first()
            if dest is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination store not found.")

        fulfillment_store_id = payload.fulfillment_store_id
        if fulfillment_store_id is None:
            first_item = payload.items[0]
            best_store = conn.execute(
                text(
                    """
                    SELECT store_id
                    FROM retail_demo.inventory
                    WHERE sku_id = :sku_id
                      AND available_qty >= :quantity
                    ORDER BY available_qty DESC
                    LIMIT 1
                    """
                ),
                {"sku_id": first_item.sku_id, "quantity": first_item.quantity},
            ).mappings().first()
            if best_store is None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No store can fulfill requested item.")
            fulfillment_store_id = int(best_store["store_id"])

        for item in payload.items:
            inv = conn.execute(
                text(
                    """
                    SELECT available_qty
                    FROM retail_demo.inventory
                    WHERE store_id = :store_id
                      AND sku_id = :sku_id
                    """
                ),
                {"store_id": fulfillment_store_id, "sku_id": item.sku_id},
            ).mappings().first()
            if inv is None or inv["available_qty"] < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient inventory for {item.sku_id} in fulfillment store.",
                )

        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        days = 1 if payload.shipping_method == "store_pickup" else 3
        if payload.shipping_method == "expedited":
            days = 2
        if payload.shipping_method == "overnight":
            days = 1
        if payload.destination_store_id is not None and payload.destination_store_id == fulfillment_store_id:
            days = 1
        eta_date = (datetime.now(timezone.utc) + timedelta(days=days)).date()

        conn.execute(
            text(
                """
                INSERT INTO retail_demo.orders (
                    order_id, customer_id, order_status, fulfillment_store_id,
                    destination_store_id, ship_to_city, shipping_method,
                    estimated_delivery_days, estimated_delivery_date
                )
                VALUES (
                    :order_id, :customer_id, 'placed', :fulfillment_store_id,
                    :destination_store_id, :ship_to_city, :shipping_method,
                    :estimated_delivery_days, :estimated_delivery_date
                )
                """
            ),
            {
                "order_id": order_id,
                "customer_id": payload.customer_id,
                "fulfillment_store_id": fulfillment_store_id,
                "destination_store_id": payload.destination_store_id,
                "ship_to_city": payload.ship_to_city,
                "shipping_method": payload.shipping_method,
                "estimated_delivery_days": days,
                "estimated_delivery_date": eta_date,
            },
        )

        for item in payload.items:
            price = conn.execute(
                text("SELECT msrp FROM retail_demo.products WHERE sku_id = :sku_id"),
                {"sku_id": item.sku_id},
            ).mappings().first()
            if price is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SKU not found: {item.sku_id}")

            conn.execute(
                text(
                    """
                    INSERT INTO retail_demo.order_line_items (order_id, sku_id, quantity, unit_price)
                    VALUES (:order_id, :sku_id, :quantity, :unit_price)
                    """
                ),
                {
                    "order_id": order_id,
                    "sku_id": item.sku_id,
                    "quantity": item.quantity,
                    "unit_price": price["msrp"],
                },
            )

            conn.execute(
                text(
                    """
                    UPDATE retail_demo.inventory
                    SET
                        reserved_qty = reserved_qty + :quantity,
                        available_qty = on_hand_qty - (reserved_qty + :quantity),
                        last_updated = NOW()
                    WHERE store_id = :store_id
                      AND sku_id = :sku_id
                    """
                ),
                {"quantity": item.quantity, "store_id": fulfillment_store_id, "sku_id": item.sku_id},
            )

    return _build_order_response(order_id)


@app.get(
    "/orders/{order_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get order status and estimated delivery timeline",
    response_model=OrderResponse,
)
def get_order(order_id: str) -> OrderResponse:
    return _build_order_response(order_id)


@app.get(
    "/performance/weekly",
    dependencies=[Depends(require_api_key)],
    summary="Get weekly category or style performance",
    response_model=WeeklyPerformanceResponse,
)
def get_weekly_performance(
    category: str | None = None,
    style_id: str | None = None,
    store_id: int | None = None,
    week_start_from: date | None = None,
    week_start_to: date | None = None,
) -> WeeklyPerformanceResponse:
    rows = _fetch_all(
        """
        SELECT
            p.week_start_date,
            p.store_id,
            s.store_name,
            pr.category,
            p.style_id,
            p.units_sold,
            p.net_sales::float AS net_sales,
            p.gross_margin::float AS gross_margin,
            p.markdown_rate::float AS markdown_rate,
            p.sell_through_pct::float AS sell_through_pct,
            p.weeks_of_supply::float AS weeks_of_supply
        FROM retail_demo.weekly_performance_summary p
        JOIN retail_demo.stores s ON s.store_id = p.store_id
        JOIN (
            SELECT DISTINCT style_id, category
            FROM retail_demo.products
        ) pr ON pr.style_id = p.style_id
        WHERE (:category IS NULL OR pr.category = :category)
          AND (:style_id IS NULL OR p.style_id = :style_id)
          AND (:store_id IS NULL OR p.store_id = :store_id)
          AND (:week_start_from IS NULL OR p.week_start_date >= :week_start_from)
          AND (:week_start_to IS NULL OR p.week_start_date <= :week_start_to)
        ORDER BY p.week_start_date DESC, p.store_id, p.style_id
        """,
        {
            "category": category,
            "style_id": style_id,
            "store_id": store_id,
            "week_start_from": week_start_from,
            "week_start_to": week_start_to,
        },
    )
    return WeeklyPerformanceResponse(performance=[WeeklyPerformanceRecord(**row) for row in rows])


@app.get(
    "/planning/inventory-imbalance",
    dependencies=[Depends(require_api_key)],
    summary="Identify inventory shortages and surpluses by location",
    response_model=InventoryImbalanceResponse,
)
def get_inventory_imbalance(
    category: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
) -> InventoryImbalanceResponse:
    rows = _fetch_all(
        """
        WITH inv AS (
            SELECT
                i.store_id,
                s.store_name,
                i.sku_id,
                i.available_qty,
                p.style_id,
                p.product_name,
                p.category
            FROM retail_demo.inventory i
            JOIN retail_demo.stores s ON s.store_id = i.store_id
            JOIN retail_demo.products p ON p.sku_id = i.sku_id
            WHERE (:category IS NULL OR p.category = :category)
        )
        SELECT
            short.sku_id,
            short.style_id,
            short.product_name,
            short.category,
            short.store_id AS shortage_store_id,
            short.store_name AS shortage_store_name,
            short.available_qty AS shortage_available_qty,
            surplus.store_id AS surplus_store_id,
            surplus.store_name AS surplus_store_name,
            surplus.available_qty AS surplus_available_qty
        FROM inv short
        JOIN inv surplus
          ON short.sku_id = surplus.sku_id
         AND short.store_id <> surplus.store_id
        WHERE short.available_qty = 0
          AND surplus.available_qty > 0
        ORDER BY surplus.available_qty DESC, short.style_id
        LIMIT :limit
        """,
        {"category": category, "limit": limit},
    )
    return InventoryImbalanceResponse(imbalances=[InventoryImbalanceRecord(**row) for row in rows])


@app.get(
    "/planning/recommendations",
    dependencies=[Depends(require_api_key)],
    summary="Recommend transfer, markdown, or reorder actions",
    response_model=PlanningRecommendationsResponse,
)
def get_planning_recommendations(
    category: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
) -> PlanningRecommendationsResponse:
    rows = _fetch_all(
        """
        WITH perf AS (
            SELECT
                p.store_id,
                s.store_name,
                p.style_id,
                pr.category,
                AVG(p.sell_through_pct)::float AS avg_sell_through,
                AVG(p.weeks_of_supply)::float AS avg_wos
            FROM retail_demo.weekly_performance_summary p
            JOIN retail_demo.stores s ON s.store_id = p.store_id
            JOIN (
                SELECT DISTINCT style_id, category
                FROM retail_demo.products
            ) pr ON pr.style_id = p.style_id
            WHERE (:category IS NULL OR pr.category = :category)
            GROUP BY p.store_id, s.store_name, p.style_id, pr.category
        ),
        style_inv AS (
            SELECT
                i.store_id,
                p.style_id,
                SUM(i.available_qty)::int AS style_available_qty
            FROM retail_demo.inventory i
            JOIN retail_demo.products p ON p.sku_id = i.sku_id
            GROUP BY i.store_id, p.style_id
        ),
        transfer_candidates AS (
            SELECT
                'transfer'::text AS action_type,
                'high'::text AS priority,
                dst.style_id,
                dst.category,
                src.store_id AS source_store_id,
                src.store_name AS source_store_name,
                dst.store_id AS target_store_id,
                dst.store_name AS target_store_name,
                LEAST(COALESCE(src_inv.style_available_qty, 0), 3)::int AS recommended_units,
                ('Demand is high in ' || dst.store_name || ' with low supply; move inventory from ' || src.store_name || '.')::text AS rationale
            FROM perf dst
            JOIN perf src ON src.style_id = dst.style_id AND src.store_id <> dst.store_id
            LEFT JOIN style_inv dst_inv ON dst_inv.store_id = dst.store_id AND dst_inv.style_id = dst.style_id
            LEFT JOIN style_inv src_inv ON src_inv.store_id = src.store_id AND src_inv.style_id = src.style_id
            WHERE dst.avg_sell_through >= 65
              AND dst.avg_wos <= 1.5
              AND COALESCE(dst_inv.style_available_qty, 0) = 0
              AND COALESCE(src_inv.style_available_qty, 0) >= 3
        ),
        markdown_candidates AS (
            SELECT
                'markdown_adjustment'::text AS action_type,
                'medium'::text AS priority,
                p.style_id,
                p.category,
                p.store_id AS source_store_id,
                p.store_name AS source_store_name,
                NULL::int AS target_store_id,
                NULL::text AS target_store_name,
                NULL::int AS recommended_units,
                ('Low sell-through and high weeks of supply suggest deeper markdown testing in ' || p.store_name || '.')::text AS rationale
            FROM perf p
            WHERE p.avg_sell_through <= 35
              AND p.avg_wos >= 5
        ),
        reorder_candidates AS (
            SELECT
                'reorder'::text AS action_type,
                'high'::text AS priority,
                p.style_id,
                p.category,
                NULL::int AS source_store_id,
                NULL::text AS source_store_name,
                p.store_id AS target_store_id,
                p.store_name AS target_store_name,
                4::int AS recommended_units,
                ('Strong demand and low weeks of supply support a reorder for ' || p.store_name || '.')::text AS rationale
            FROM perf p
            WHERE p.avg_sell_through >= 70
              AND p.avg_wos <= 1.5
        )
        SELECT * FROM transfer_candidates
        UNION ALL
        SELECT * FROM markdown_candidates
        UNION ALL
        SELECT * FROM reorder_candidates
        ORDER BY
            CASE priority WHEN 'high' THEN 0 ELSE 1 END,
            action_type,
            style_id
        LIMIT :limit
        """,
        {"category": category, "limit": limit},
    )
    return PlanningRecommendationsResponse(
        recommendations=[PlanningRecommendationRecord(**row) for row in rows]
    )
