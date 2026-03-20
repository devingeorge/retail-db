import os
import re
from datetime import datetime
from typing import Any

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
    title="Retail DB GPT Actions API",
    version="0.1.0",
    description=(
        "Local API for ChatGPT GPT Actions to inspect database schemas and tables. "
        "This starter intentionally provides read-only metadata endpoints."
    ),
    servers=[{"url": PUBLIC_BASE_URL}] if PUBLIC_BASE_URL else [],
)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def require_api_key(x_api_key: str | None = Security(api_key_header)) -> None:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
        )
    if x_api_key != ACTIONS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


class SchemaCreateRequest(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class HealthResponse(BaseModel):
    status: str


class SchemasResponse(BaseModel):
    schemas: list[str]


class SchemaTablesResponse(BaseModel):
    schema: str
    tables: list[str]


class SchemaCreateResponse(BaseModel):
    created: str


class CustomerProfileResponse(BaseModel):
    customer_id: int
    loyalty_id: str
    email: str
    first_name: str
    last_name: str
    tier: str
    preferred_store_id: int | None
    preferred_sizes: list[str]
    preferred_colors: list[str]
    preferred_brands: list[str]
    shopping_occasions: list[str]
    recent_purchases: list[dict[str, Any]]
    saved_items: list[dict[str, Any]]
    return_history_summary: dict[str, Any]
    stylist_notes: str
    lifetime_value_band: str


class RecentPurchasesResponse(BaseModel):
    customer_id: int
    last_purchase_ts: datetime | None
    recent_purchases: list[dict[str, Any]]


class SavedItemsResponse(BaseModel):
    customer_id: int
    saved_item_count: int
    saved_items: list[dict[str, Any]]


class ReturnSummaryResponse(BaseModel):
    customer_id: int
    total_returns: int
    avg_refund_amount: float | None
    total_refund_amount: float | None
    return_history_summary: dict[str, Any]


class LifetimeValueBandItem(BaseModel):
    lifetime_value_band: str
    customer_count: int


class LifetimeValueBandsResponse(BaseModel):
    bands: list[LifetimeValueBandItem]


class StyleSummary(BaseModel):
    style_id: str
    style_name: str
    category: str
    season: str
    planned_cc_count: int
    core_vs_fashion: str
    strategic_priority: str


class StyleSearchResponse(BaseModel):
    styles: list[StyleSummary]


class StyleSkuItem(BaseModel):
    sku: str
    style_id: str
    style_name: str
    category: str
    color_name: str
    size: str
    msrp: float
    cost: float
    substitute_style_id: str | None
    trade_up_style_id: str | None


class StyleSkusResponse(BaseModel):
    skus: list[StyleSkuItem]


class InventoryItem(BaseModel):
    store_id: int
    store_name: str
    region: str
    sku: str
    style_id: str
    style_name: str
    color_name: str
    size: str
    msrp: float
    on_hand_units: int
    available_for_transfer: bool
    available_online_dc: int


class InventoryResponse(BaseModel):
    inventory: list[InventoryItem]


class TransferOption(BaseModel):
    source_store_id: int
    source_store_name: str
    source_region: str
    on_hand_units: int
    available_online_dc: int
    available_for_transfer: bool
    rank_reason: str


class TransferOptionsResponse(BaseModel):
    sku: str
    origin_store_id: int
    transfer_options: list[TransferOption]


class AlternativeOption(BaseModel):
    relationship_type: str
    sku: str
    style_id: str
    style_name: str
    category: str
    color_name: str
    size: str
    msrp: float
    store_id: int
    store_name: str
    region: str
    on_hand_units: int
    available_for_transfer: bool
    available_online_dc: int


class AlternativesResponse(BaseModel):
    source_style_id: str
    alternatives: list[AlternativeOption]


class CrossSellOption(BaseModel):
    relationship_type: str
    rationale: str | None
    priority_rank: int
    sku: str
    style_id: str
    style_name: str
    category: str
    color_name: str
    size: str
    msrp: float
    store_id: int
    store_name: str
    region: str
    on_hand_units: int
    available_for_transfer: bool
    available_online_dc: int


class CrossSellResponse(BaseModel):
    source_style_id: str
    cross_sells: list[CrossSellOption]


class StoreLocationResponse(BaseModel):
    store_id: int
    store_name: str
    region: str
    state_code: str
    city: str
    street_address: str | None
    postal_code: str | None


class OrderItemCreateRequest(BaseModel):
    sku: str
    quantity: int = Field(..., ge=1, le=50)


class OrderCreateRequest(BaseModel):
    customer_id: int
    store_id: int
    items: list[OrderItemCreateRequest] = Field(..., min_length=1)
    associate_note: str | None = Field(default=None, max_length=500)


class OrderItemResponse(BaseModel):
    sku: str
    quantity: int
    unit_price: float
    line_total: float


class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    customer_name: str
    store_id: int
    store_name: str
    order_status: str
    order_source: str
    associate_note: str | None
    created_at: datetime
    total_amount: float
    items: list[OrderItemResponse]


@app.get("/health", summary="Health check", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/schemas",
    dependencies=[Depends(require_api_key)],
    summary="List available database schemas",
    response_model=SchemasResponse,
)
def list_schemas() -> SchemasResponse:
    query = text(
        """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query).all()

    return SchemasResponse(schemas=[row[0] for row in rows])


@app.get(
    "/schemas/{schema_name}/tables",
    dependencies=[Depends(require_api_key)],
    summary="List tables for a schema",
    response_model=SchemaTablesResponse,
)
def list_tables(schema_name: str) -> SchemaTablesResponse:
    query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema_name
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, {"schema_name": schema_name}).all()

    return SchemaTablesResponse(schema=schema_name, tables=[row[0] for row in rows])


@app.post(
    "/schemas",
    dependencies=[Depends(require_api_key)],
    summary="Create a new schema",
    response_model=SchemaCreateResponse,
)
def create_schema(payload: SchemaCreateRequest) -> SchemaCreateResponse:
    # Schema names cannot be parameterized as identifiers, so we validate strictly first.
    schema_name = payload.name
    query = text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')

    with engine.begin() as conn:
        conn.execute(query)

    return SchemaCreateResponse(created=schema_name)


def _fetch_one_or_404(query_text: str, params: dict, not_found_message: str) -> dict:
    query = text(query_text)
    with engine.connect() as conn:
        row = conn.execute(query, params).mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message)
    return dict(row)


def _fetch_all(query_text: str, params: dict | None = None) -> list[dict]:
    query = text(query_text)
    with engine.connect() as conn:
        rows = conn.execute(query, params or {}).mappings().all()
    return [dict(row) for row in rows]


def _normalize_style_id(style_id: str) -> str:
    """
    Accept style identifiers in several common forms and normalize to STY-####.
    Examples:
    - STY-0219 -> STY-0219
    - 0219 -> STY-0219
    - Athleisure Style 0219 -> STY-0219
    """
    normalized = style_id.strip().upper()
    if normalized.startswith("STY-"):
        suffix = normalized[4:]
        if suffix.isdigit():
            return f"STY-{int(suffix):04d}"
        return normalized
    if normalized.isdigit():
        return f"STY-{int(normalized):04d}"
    match = re.search(r"(\d{1,4})$", normalized)
    if match:
        return f"STY-{int(match.group(1)):04d}"
    return normalized


def _build_order_response(order_id: int) -> OrderResponse:
    header = _fetch_one_or_404(
        """
        SELECT
            o.order_id,
            o.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
            o.store_id,
            s.store_name,
            o.order_status,
            o.order_source,
            o.associate_note,
            o.created_at,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0)::float AS total_amount
        FROM "ORDERS".orders o
        JOIN retail_core.customers c ON c.customer_id = o.customer_id
        JOIN retail_core.stores s ON s.store_id = o.store_id
        LEFT JOIN "ORDERS".order_items oi ON oi.order_id = o.order_id
        WHERE o.order_id = :order_id
        GROUP BY
            o.order_id,
            o.customer_id,
            c.first_name,
            c.last_name,
            o.store_id,
            s.store_name,
            o.order_status,
            o.order_source,
            o.associate_note,
            o.created_at
        """,
        {"order_id": order_id},
        "Order not found.",
    )

    item_rows = _fetch_all(
        """
        SELECT
            sku,
            quantity,
            unit_price::float AS unit_price,
            (quantity * unit_price)::float AS line_total
        FROM "ORDERS".order_items
        WHERE order_id = :order_id
        ORDER BY order_item_id
        """,
        {"order_id": order_id},
    )

    return OrderResponse(
        **header,
        items=[OrderItemResponse(**row) for row in item_rows],
    )


@app.get(
    "/stores/{store_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get physical store location details by store ID",
    response_model=StoreLocationResponse,
)
def get_store_location(store_id: int) -> StoreLocationResponse:
    row = _fetch_one_or_404(
        """
        SELECT
            store_id,
            store_name,
            region,
            state_code,
            city,
            street_address,
            postal_code
        FROM retail_core.stores
        WHERE store_id = :store_id
        """,
        {"store_id": store_id},
        "Store not found.",
    )
    return StoreLocationResponse(**row)


@app.get(
    "/customers/{customer_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get full customer 360 profile by customer ID",
    response_model=CustomerProfileResponse,
)
def get_customer_profile(customer_id: int) -> CustomerProfileResponse:
    row = _fetch_one_or_404(
        """
        SELECT
            customer_id,
            loyalty_id,
            email,
            first_name,
            last_name,
            tier,
            preferred_store_id,
            preferred_sizes,
            preferred_colors,
            preferred_brands,
            shopping_occasions,
            recent_purchases,
            saved_items,
            return_history_summary,
            stylist_notes,
            lifetime_value_band
        FROM retail_analytics.customer_360
        WHERE customer_id = :customer_id
        """,
        {"customer_id": customer_id},
        "Customer not found.",
    )
    return CustomerProfileResponse(**row)


@app.get(
    "/customers/by-loyalty/{loyalty_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get full customer 360 profile by loyalty ID",
    response_model=CustomerProfileResponse,
)
def get_customer_profile_by_loyalty(loyalty_id: str) -> CustomerProfileResponse:
    row = _fetch_one_or_404(
        """
        SELECT
            customer_id,
            loyalty_id,
            email,
            first_name,
            last_name,
            tier,
            preferred_store_id,
            preferred_sizes,
            preferred_colors,
            preferred_brands,
            shopping_occasions,
            recent_purchases,
            saved_items,
            return_history_summary,
            stylist_notes,
            lifetime_value_band
        FROM retail_analytics.customer_360
        WHERE loyalty_id = :loyalty_id
        """,
        {"loyalty_id": loyalty_id},
        "Customer not found.",
    )
    return CustomerProfileResponse(**row)


@app.get(
    "/customers/email/{email}",
    dependencies=[Depends(require_api_key)],
    summary="Get full customer 360 profile by email",
    response_model=CustomerProfileResponse,
)
def get_customer_profile_by_email(email: str) -> CustomerProfileResponse:
    row = _fetch_one_or_404(
        """
        SELECT
            customer_id,
            loyalty_id,
            email,
            first_name,
            last_name,
            tier,
            preferred_store_id,
            preferred_sizes,
            preferred_colors,
            preferred_brands,
            shopping_occasions,
            recent_purchases,
            saved_items,
            return_history_summary,
            stylist_notes,
            lifetime_value_band
        FROM retail_analytics.customer_360
        WHERE LOWER(email) = LOWER(:email)
        """,
        {"email": email},
        "Customer not found.",
    )
    return CustomerProfileResponse(**row)


@app.get(
    "/customers/{customer_id}/recent-purchases",
    dependencies=[Depends(require_api_key)],
    summary="Get a customer's recent purchases",
    response_model=RecentPurchasesResponse,
)
def get_recent_purchases(customer_id: int) -> RecentPurchasesResponse:
    result = _fetch_one_or_404(
        """
        SELECT customer_id, last_purchase_ts, recent_purchases
        FROM retail_analytics.customer_recent_purchases
        WHERE customer_id = :customer_id
        """,
        {"customer_id": customer_id},
        "Recent purchases not found for customer.",
    )
    return RecentPurchasesResponse(**result)


@app.get(
    "/customers/{customer_id}/saved-items",
    dependencies=[Depends(require_api_key)],
    summary="Get a customer's saved items summary",
    response_model=SavedItemsResponse,
)
def get_saved_items(customer_id: int) -> SavedItemsResponse:
    result = _fetch_one_or_404(
        """
        SELECT customer_id, saved_item_count, saved_items
        FROM retail_analytics.customer_saved_items_summary
        WHERE customer_id = :customer_id
        """,
        {"customer_id": customer_id},
        "Saved items not found for customer.",
    )
    return SavedItemsResponse(**result)


@app.get(
    "/customers/{customer_id}/return-summary",
    dependencies=[Depends(require_api_key)],
    summary="Get a customer's return history summary",
    response_model=ReturnSummaryResponse,
)
def get_return_summary(customer_id: int) -> ReturnSummaryResponse:
    result = _fetch_one_or_404(
        """
        SELECT
            customer_id,
            total_returns,
            avg_refund_amount,
            total_refund_amount,
            return_history_summary
        FROM retail_analytics.customer_return_history_summary
        WHERE customer_id = :customer_id
        """,
        {"customer_id": customer_id},
        "Return history not found for customer.",
    )
    return ReturnSummaryResponse(**result)


@app.get(
    "/analytics/lifetime-value-bands",
    dependencies=[Depends(require_api_key)],
    summary="Get customer counts by lifetime value band",
    response_model=LifetimeValueBandsResponse,
)
def get_lifetime_value_band_breakdown() -> LifetimeValueBandsResponse:
    query = text(
        """
        SELECT lifetime_value_band, COUNT(*) AS customer_count
        FROM retail_core.customers
        GROUP BY lifetime_value_band
        ORDER BY customer_count DESC
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return LifetimeValueBandsResponse(
        bands=[LifetimeValueBandItem(**dict(row)) for row in rows]
    )


@app.get(
    "/styles/search",
    dependencies=[Depends(require_api_key)],
    summary="Search styles by style name",
    response_model=StyleSearchResponse,
)
def search_styles_by_name(
    style_name: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
) -> StyleSearchResponse:
    rows = _fetch_all(
        """
        SELECT
            style_id,
            style_name,
            category,
            season,
            planned_cc_count,
            core_vs_fashion,
            strategic_priority
        FROM retail_usecases.styles
        WHERE style_name ILIKE :style_name_pattern
        ORDER BY style_name
        LIMIT :limit
        """,
        {"style_name_pattern": f"%{style_name}%", "limit": limit},
    )
    return StyleSearchResponse(styles=[StyleSummary(**row) for row in rows])


@app.get(
    "/styles/{style_id}/skus",
    dependencies=[Depends(require_api_key)],
    summary="List SKU variants for a style",
    response_model=StyleSkusResponse,
)
def get_style_skus(style_id: str) -> StyleSkusResponse:
    normalized_style_id = _normalize_style_id(style_id)
    rows = _fetch_all(
        """
        SELECT
            s.sku,
            s.style_id,
            st.style_name,
            st.category,
            s.color_name,
            s.size,
            s.msrp,
            s.cost,
            s.substitute_style_id,
            s.trade_up_style_id
        FROM retail_usecases.skus s
        JOIN retail_usecases.styles st ON st.style_id = s.style_id
        WHERE s.style_id = :style_id
        ORDER BY s.sku
        """,
        {"style_id": normalized_style_id},
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style or SKUs not found.")
    return StyleSkusResponse(skus=[StyleSkuItem(**row) for row in rows])


@app.get(
    "/inventory/style/{style_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get inventory for all SKUs in a style",
    response_model=InventoryResponse,
)
def get_inventory_by_style(style_id: str) -> InventoryResponse:
    normalized_style_id = _normalize_style_id(style_id)
    rows = _fetch_all(
        """
        SELECT
            i.store_id,
            i.store_name,
            i.region,
            i.sku,
            s.style_id,
            st.style_name,
            s.color_name,
            s.size,
            s.msrp,
            i.on_hand_units,
            i.available_for_transfer,
            i.available_online_dc
        FROM retail_usecases.inventory i
        JOIN retail_usecases.skus s ON s.sku = i.sku
        JOIN retail_usecases.styles st ON st.style_id = s.style_id
        WHERE s.style_id = :style_id
        ORDER BY i.on_hand_units DESC, i.available_online_dc DESC
        """,
        {"style_id": normalized_style_id},
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory found for style.")
    return InventoryResponse(inventory=[InventoryItem(**row) for row in rows])


@app.get(
    "/inventory/style/{style_id}/size/{size}",
    dependencies=[Depends(require_api_key)],
    summary="Get inventory for a style filtered by size",
    response_model=InventoryResponse,
)
def get_inventory_by_style_and_size(style_id: str, size: str) -> InventoryResponse:
    normalized_style_id = _normalize_style_id(style_id)
    rows = _fetch_all(
        """
        SELECT
            i.store_id,
            i.store_name,
            i.region,
            i.sku,
            s.style_id,
            st.style_name,
            s.color_name,
            s.size,
            s.msrp,
            i.on_hand_units,
            i.available_for_transfer,
            i.available_online_dc
        FROM retail_usecases.inventory i
        JOIN retail_usecases.skus s ON s.sku = i.sku
        JOIN retail_usecases.styles st ON st.style_id = s.style_id
        WHERE s.style_id = :style_id
          AND s.size = :size
        ORDER BY i.on_hand_units DESC, i.available_online_dc DESC
        """,
        {"style_id": normalized_style_id, "size": size},
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory found for style and size.")
    return InventoryResponse(inventory=[InventoryItem(**row) for row in rows])


@app.get(
    "/inventory/sku/{sku}",
    dependencies=[Depends(require_api_key)],
    summary="Get inventory by exact SKU",
    response_model=InventoryResponse,
)
def get_inventory_by_sku(sku: str) -> InventoryResponse:
    rows = _fetch_all(
        """
        SELECT
            i.store_id,
            i.store_name,
            i.region,
            i.sku,
            s.style_id,
            st.style_name,
            s.color_name,
            s.size,
            s.msrp,
            i.on_hand_units,
            i.available_for_transfer,
            i.available_online_dc
        FROM retail_usecases.inventory i
        JOIN retail_usecases.skus s ON s.sku = i.sku
        JOIN retail_usecases.styles st ON st.style_id = s.style_id
        WHERE i.sku = :sku
        ORDER BY i.on_hand_units DESC, i.available_online_dc DESC
        """,
        {"sku": sku},
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory found for SKU.")
    return InventoryResponse(inventory=[InventoryItem(**row) for row in rows])


@app.get(
    "/inventory/transfer-options",
    dependencies=[Depends(require_api_key)],
    summary="Rank transfer options for a SKU from an origin store",
    response_model=TransferOptionsResponse,
)
def get_transfer_options(
    sku: str,
    origin_store_id: int,
    limit: int = Query(5, ge=1, le=20),
) -> TransferOptionsResponse:
    origin = _fetch_one_or_404(
        """
        SELECT store_id, region
        FROM retail_usecases.inventory
        WHERE store_id = :origin_store_id
          AND sku = :sku
        LIMIT 1
        """,
        {"origin_store_id": origin_store_id, "sku": sku},
        "Origin store inventory for SKU not found.",
    )

    rows = _fetch_all(
        """
        SELECT
            i.store_id AS source_store_id,
            i.store_name AS source_store_name,
            i.region AS source_region,
            i.on_hand_units,
            i.available_online_dc,
            i.available_for_transfer
        FROM retail_usecases.inventory i
        WHERE i.sku = :sku
          AND i.store_id <> :origin_store_id
          AND i.on_hand_units > 0
          AND i.available_for_transfer = TRUE
        ORDER BY
            CASE WHEN i.region = :origin_region THEN 0 ELSE 1 END,
            i.on_hand_units DESC,
            i.available_online_dc DESC
        LIMIT :limit
        """,
        {
            "sku": sku,
            "origin_store_id": origin_store_id,
            "origin_region": origin["region"],
            "limit": limit,
        },
    )

    options: list[TransferOption] = []
    for row in rows:
        rank_reason = (
            "same region, high stock"
            if row["source_region"] == origin["region"]
            else "cross-region availability"
        )
        options.append(TransferOption(**row, rank_reason=rank_reason))

    return TransferOptionsResponse(
        sku=sku,
        origin_store_id=origin_store_id,
        transfer_options=options,
    )


@app.get(
    "/styles/{style_id}/alternatives",
    dependencies=[Depends(require_api_key)],
    summary="Find substitute and trade-up alternatives with inventory",
    response_model=AlternativesResponse,
)
def get_style_alternatives(
    style_id: str,
    size: str | None = None,
    preferred_colors: str | None = Query(
        default=None, description="Comma-separated colors, e.g. Blue,Beige"
    ),
    origin_store_id: int | None = None,
    limit: int = Query(10, ge=1, le=50),
) -> AlternativesResponse:
    normalized_style_id = _normalize_style_id(style_id)
    rows = _fetch_all(
        """
        WITH refs AS (
            SELECT DISTINCT substitute_style_id AS ref_style_id, 'substitute' AS relationship_type
            FROM retail_usecases.skus
            WHERE style_id = :style_id
              AND substitute_style_id IS NOT NULL
            UNION ALL
            SELECT DISTINCT trade_up_style_id AS ref_style_id, 'trade_up' AS relationship_type
            FROM retail_usecases.skus
            WHERE style_id = :style_id
              AND trade_up_style_id IS NOT NULL
        )
        SELECT
            r.relationship_type,
            s.sku,
            s.style_id,
            st.style_name,
            st.category,
            s.color_name,
            s.size,
            s.msrp,
            i.store_id,
            i.store_name,
            i.region,
            i.on_hand_units,
            i.available_for_transfer,
            i.available_online_dc
        FROM refs r
        JOIN retail_usecases.skus s ON s.style_id = r.ref_style_id
        JOIN retail_usecases.styles st ON st.style_id = s.style_id
        JOIN retail_usecases.inventory i ON i.sku = s.sku
        WHERE i.on_hand_units > 0
          AND (:size IS NULL OR s.size = :size)
          AND (:origin_store_id IS NULL OR i.store_id = :origin_store_id)
        ORDER BY
            CASE WHEN r.relationship_type = 'substitute' THEN 0 ELSE 1 END,
            i.on_hand_units DESC,
            i.available_online_dc DESC
        LIMIT :limit
        """,
        {
            "style_id": normalized_style_id,
            "size": size,
            "origin_store_id": origin_store_id,
            "limit": limit,
        },
    )

    preferred_color_set: set[str] | None = None
    if preferred_colors:
        preferred_color_set = {color.strip().lower() for color in preferred_colors.split(",") if color.strip()}

    options: list[AlternativeOption] = []
    for row in rows:
        if preferred_color_set and row["color_name"].lower() not in preferred_color_set:
            continue
        options.append(AlternativeOption(**row))

    return AlternativesResponse(source_style_id=normalized_style_id, alternatives=options)


@app.get(
    "/styles/{style_id}/cross-sell",
    dependencies=[Depends(require_api_key)],
    summary="Find cross-sell styles with inventory for a source style",
    response_model=CrossSellResponse,
)
def get_style_cross_sell(
    style_id: str,
    size: str | None = None,
    preferred_colors: str | None = Query(
        default=None, description="Comma-separated colors, e.g. Blue,Beige"
    ),
    origin_store_id: int | None = None,
    limit: int = Query(10, ge=1, le=50),
) -> CrossSellResponse:
    normalized_style_id = _normalize_style_id(style_id)
    rows = _fetch_all(
        """
        SELECT
            rel.relationship_type,
            rel.rationale,
            rel.priority_rank,
            s.sku,
            s.style_id,
            st.style_name,
            st.category,
            s.color_name,
            s.size,
            s.msrp,
            i.store_id,
            i.store_name,
            i.region,
            i.on_hand_units,
            i.available_for_transfer,
            i.available_online_dc
        FROM retail_usecases.style_relationships rel
        JOIN retail_usecases.skus s ON s.style_id = rel.to_style_id
        JOIN retail_usecases.styles st ON st.style_id = s.style_id
        JOIN retail_usecases.inventory i ON i.sku = s.sku
        WHERE rel.from_style_id = :style_id
          AND rel.relationship_type = 'cross_sell'
          AND i.on_hand_units > 0
          AND (:size IS NULL OR s.size = :size)
          AND (:origin_store_id IS NULL OR i.store_id = :origin_store_id)
        ORDER BY
            rel.priority_rank ASC,
            i.on_hand_units DESC,
            i.available_online_dc DESC
        LIMIT :limit
        """,
        {
            "style_id": normalized_style_id,
            "size": size,
            "origin_store_id": origin_store_id,
            "limit": limit,
        },
    )

    preferred_color_set: set[str] | None = None
    if preferred_colors:
        preferred_color_set = {color.strip().lower() for color in preferred_colors.split(",") if color.strip()}

    options: list[CrossSellOption] = []
    for row in rows:
        if preferred_color_set and row["color_name"].lower() not in preferred_color_set:
            continue
        options.append(CrossSellOption(**row))

    return CrossSellResponse(source_style_id=normalized_style_id, cross_sells=options)


@app.post(
    "/orders",
    dependencies=[Depends(require_api_key)],
    summary="Create an order in the ORDERS schema",
    response_model=OrderResponse,
)
def create_order(payload: OrderCreateRequest) -> OrderResponse:
    with engine.begin() as conn:
        customer = conn.execute(
            text("SELECT customer_id FROM retail_core.customers WHERE customer_id = :customer_id"),
            {"customer_id": payload.customer_id},
        ).mappings().first()
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        store = conn.execute(
            text("SELECT store_id FROM retail_core.stores WHERE store_id = :store_id"),
            {"store_id": payload.store_id},
        ).mappings().first()
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found.")

        created = conn.execute(
            text(
                """
                INSERT INTO "ORDERS".orders (customer_id, store_id, order_status, order_source, associate_note)
                VALUES (:customer_id, :store_id, 'pending', 'gpt_action', :associate_note)
                RETURNING order_id
                """
            ),
            {
                "customer_id": payload.customer_id,
                "store_id": payload.store_id,
                "associate_note": payload.associate_note,
            },
        ).mappings().first()
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create order.",
            )
        order_id = int(created["order_id"])

        for item in payload.items:
            price_row = conn.execute(
                text(
                    """
                    SELECT msrp::float AS unit_price
                    FROM retail_usecases.skus
                    WHERE sku = :sku
                    """
                ),
                {"sku": item.sku},
            ).mappings().first()
            if price_row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"SKU not found: {item.sku}",
                )

            conn.execute(
                text(
                    """
                    INSERT INTO "ORDERS".order_items (order_id, sku, quantity, unit_price)
                    VALUES (:order_id, :sku, :quantity, :unit_price)
                    """
                ),
                {
                    "order_id": order_id,
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "unit_price": price_row["unit_price"],
                },
            )

    return _build_order_response(order_id)


@app.get(
    "/orders/{order_id}",
    dependencies=[Depends(require_api_key)],
    summary="Get an order from the ORDERS schema",
    response_model=OrderResponse,
)
def get_order(order_id: int) -> OrderResponse:
    return _build_order_response(order_id)
