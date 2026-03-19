import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
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


def require_api_key(x_api_key: str = Header(...)) -> None:
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
