#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${1:-$ROOT_DIR/data/generated/q4_2025}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT_DIR/.env"
  set +a
fi

if [[ -z "${DB_URL:-}" ]]; then
  echo "DB_URL is not set. Populate .env or export DB_URL."
  exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
  echo "Data directory not found: $DATA_DIR"
  exit 1
fi

echo "Using data directory: $DATA_DIR"
echo "Creating schemas/tables..."
psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/sql/010_create_retail_tables.sql"

echo "Truncating existing retail tables..."
psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/sql/015_truncate_for_reload.sql"

echo "Loading static CSV tables (reference + core)..."
psql "$DB_URL" -v ON_ERROR_STOP=1 \
  -v "stores_csv=$DATA_DIR/reference/stores.csv" \
  -v "brands_csv=$DATA_DIR/reference/brands.csv" \
  -v "products_csv=$DATA_DIR/reference/products.csv" \
  -v "customers_csv=$DATA_DIR/core/customers.csv" \
  -v "customer_preferences_csv=$DATA_DIR/core/customer_preferences.csv" \
  -v "saved_items_csv=$DATA_DIR/core/saved_items.csv" \
  -f "$ROOT_DIR/db/sql/025_copy_static_tables.sql"

echo "Loading chunked sales CSV tables..."
for file in "$DATA_DIR"/sales/transactions_part_*.csv; do
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "\copy retail_sales.transactions(transaction_id,customer_id,store_id,transaction_ts,sales_channel,payment_method,gross_amount,discount_amount,net_amount) FROM '$file' WITH (FORMAT csv, HEADER true)"
done
for file in "$DATA_DIR"/sales/transaction_items_part_*.csv; do
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "\copy retail_sales.transaction_items(transaction_item_id,transaction_id,product_id,quantity,unit_price,discount_amount,line_total) FROM '$file' WITH (FORMAT csv, HEADER true)"
done
for file in "$DATA_DIR"/sales/returns_part_*.csv; do
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "\copy retail_sales.returns(return_id,transaction_item_id,customer_id,return_ts,reason_code,refund_amount) FROM '$file' WITH (FORMAT csv, HEADER true)"
done

echo "Building analytics structures and running maintenance..."
psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/sql/020_create_analytics_structures.sql"
psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/sql/030_post_import_maintenance.sql"

echo "Import complete."
