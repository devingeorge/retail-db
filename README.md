# Local Retail DB + GPT Actions

This project now includes:

- Local PostgreSQL with 3 schemas:
  - `retail_core`
  - `retail_sales`
  - `retail_analytics`
- A deterministic synthetic dataset generator for Q4 2025 at large scale
- High-throughput CSV import scripts (`COPY`)
- Validation SQL checks
- GPT Actions-ready API endpoints for customer profile and analytics lookups

## 1) Environment setup

```bash
cp .env.example .env
```

Set a strong `ACTIONS_API_KEY` in `.env`.

## 2) Start PostgreSQL

```bash
docker compose up -d
```

Initial schema creation comes from `db/init/001_create_schemas.sql`.

## 3) Generate synthetic Fortune-1000 dataset

Use defaults (about 10M transactions):

```bash
python3 scripts/generate_q4_dataset.py
```

Or override scale:

```bash
python3 scripts/generate_q4_dataset.py \
  --customers 750000 \
  --stores 1100 \
  --products 120000 \
  --transactions 10000000 \
  --chunk-size 1000000 \
  --seed 1001
```

Output goes to `data/generated/q4_2025` by default. See `data/README.md` for file layout.

## 4) Import generated CSV files into Postgres

```bash
chmod +x scripts/import_csv_to_postgres.sh
./scripts/import_csv_to_postgres.sh
```

If your dataset is in a non-default location:

```bash
./scripts/import_csv_to_postgres.sh /absolute/path/to/dataset
```

The import script runs:

1. `db/sql/010_create_retail_tables.sql`
2. `db/sql/015_truncate_for_reload.sql`
3. `db/sql/025_copy_static_tables.sql`
4. Chunked `\copy` for transactions, transaction items, returns
5. `db/sql/020_create_analytics_structures.sql`
6. `db/sql/030_post_import_maintenance.sql`

## 5) Validate dataset quality

Run the validation script:

```bash
psql "$DB_URL" -f db/sql/040_validation_checks.sql
```

Checks include:

- row counts
- uniqueness
- Q4 date integrity
- referential integrity spot checks
- customer 360 required-field coverage

## 6) Start API for GPT Actions

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

OpenAPI schema:

- `http://localhost:8000/openapi.json`

## 7) Connect in GPT Actions

ChatGPT Actions requires a public HTTPS endpoint. Tunnel your local API:

```bash
ngrok http 8000
```

Then configure your Action with:

- Schema URL: `https://<your-ngrok-domain>/openapi.json`
- Authentication: API key
- Header: `x-api-key`
- Value: `ACTIONS_API_KEY` from `.env`

## Optional: Deploy to Heroku

This repo includes Heroku deployment files:

- `Procfile`
- `requirements.txt` (root proxy to `api/requirements.txt`)
- `runtime.txt`

High-level flow:

1. Create app and Postgres addon.
2. Set `ACTIONS_API_KEY` config var.
3. Deploy from `main`.
4. Open:
   - `https://<your-app>.herokuapp.com/health`
   - `https://<your-app>.herokuapp.com/openapi.json`

The API supports both `DB_URL` and Heroku `DATABASE_URL` automatically.

## API endpoints

- `GET /health`
- `GET /schemas` (API key)
- `GET /schemas/{schema_name}/tables` (API key)
- `POST /schemas` (API key)
- `GET /customers/{customer_id}` (API key)
- `GET /customers/by-loyalty/{loyalty_id}` (API key)
- `GET /customers/by-email?email=<email>` (API key)
- `GET /customers/{customer_id}/recent-purchases` (API key)
- `GET /customers/{customer_id}/saved-items` (API key)
- `GET /customers/{customer_id}/return-summary` (API key)
- `GET /analytics/lifetime-value-bands` (API key)

## Data dictionary and mapping

- Required customer field mapping: `docs/customer_360_mapping.md`
