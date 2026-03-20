# Minimal Unified Retail Demo DB + GPT Actions

This project now uses a **single minimal schema** (`retail_demo`) designed to support two live demos with one GPT:

- Store associate / customer support
- Merchandising performance + planning

The model is intentionally small and hand-curated.

## 1) Environment setup

```bash
cp .env.example .env
```

Set a strong `ACTIONS_API_KEY` in `.env`.

## 2) Load the minimal demo database

Run this against your target Postgres DB:

```bash
psql "$DB_URL" -f db/sql/082_reset_and_load_minimal_demo.sql
```

This will:

1. Drop previous demo schemas (`retail_core`, `retail_sales`, `retail_analytics`, `retail_usecases`, `"ORDERS"`, and `retail_demo`).
2. Create fresh minimal tables from `db/sql/080_create_minimal_demo_tables.sql`.
3. Seed compact hand-curated demo data from `db/sql/081_seed_minimal_demo_data.sql`.

## 3) Start API for GPT Actions

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

OpenAPI schema:

- `http://localhost:8000/openapi.json`

## 4) GPT Actions configuration

For a public deployment (Heroku), use:

- App URL: `https://murmuring-bastion-19065-1f21cad4ee34.herokuapp.com`
- OpenAPI URL: `https://murmuring-bastion-19065-1f21cad4ee34.herokuapp.com/openapi.json?refresh=1`
- Auth: API key header `x-api-key`

Reference: [Getting started with GPT Actions](https://developers.openai.com/api/docs/actions/getting-started)

## 5) Endpoint surface (minimal demo)

### Associate / support

- `GET /products/search`
- `GET /products/{product_id}`
- `GET /inventory/products/{product_id}`
- `GET /inventory/products/{product_id}/stores/{store_id}`
- `GET /products/{product_id}/relationships`

### Orders

- `POST /orders`
- `GET /orders/{order_id}`

### Merch / planning

- `GET /performance/weekly`
- `GET /planning/inventory-imbalance`
- `GET /planning/recommendations`

### Utility

- `GET /health`

## 6) Data design highlights

- 3 stores: Portland, Boston, Philadelphia.
- Tiny assortment: dresses + shoes with explicit `alternative` and `complementary` links.
- Style-level weekly performance summary for planning use cases.
- SKU-level store inventory for associate and transfer workflows.
- One external image URL per product.

See detailed field descriptions in:

- `docs/minimal_demo_data_dictionary.md`
