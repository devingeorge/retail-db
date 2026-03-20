#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${1:-$ROOT_DIR/data/generated/usecases_demo_small}"
DB_CONN="${DB_URL:-}"

if [[ -z "$DB_CONN" ]]; then
  echo "DB_URL is not set. Export DB_URL before running."
  exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
  echo "Data directory not found: $DATA_DIR"
  exit 1
fi

echo "Loading use-case dataset from: $DATA_DIR"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/sql/050_create_usecase_tables.sql"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -f "$ROOT_DIR/db/sql/055_truncate_usecase_tables.sql"

psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "\copy retail_usecases.styles(style_id,style_name,category,season,planned_cc_count,core_vs_fashion,strategic_priority) FROM '$DATA_DIR/styles.csv' WITH (FORMAT csv, HEADER true)"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "\copy retail_usecases.skus(sku,style_id,color_name,size,msrp,cost,substitute_style_id,trade_up_style_id) FROM '$DATA_DIR/skus.csv' WITH (FORMAT csv, HEADER true)"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "\copy retail_usecases.inventory(store_id,store_name,region,sku,on_hand_units,available_for_transfer,available_online_dc) FROM '$DATA_DIR/inventory.csv' WITH (FORMAT csv, HEADER true)"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "\copy retail_usecases.sales_summary(period,sku,style_id,units_sold,net_sales,gross_margin_pct,sell_through_pct,markdown_rate,return_rate,store_count) FROM '$DATA_DIR/sales_summary.csv' WITH (FORMAT csv, HEADER true)"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "\copy retail_usecases.customer_profiles(customer_id,name,tier,preferred_sizes,preferred_colors,favorite_categories,recent_purchases) FROM '$DATA_DIR/customer_profiles.csv' WITH (FORMAT csv, HEADER true)"

psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "ANALYZE retail_usecases.styles"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "ANALYZE retail_usecases.skus"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "ANALYZE retail_usecases.inventory"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "ANALYZE retail_usecases.sales_summary"
psql "$DB_CONN" -v ON_ERROR_STOP=1 -c "ANALYZE retail_usecases.customer_profiles"

echo "Use-case dataset loaded."
