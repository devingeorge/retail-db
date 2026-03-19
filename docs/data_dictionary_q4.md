# Q4 2025 Synthetic Retail Dataset Dictionary

## Target scale (default generator settings)

- Customers: `750,000`
- Stores: `1,100`
- Products: `120,000`
- Transactions: `10,000,000`
- Period: `2025-10-01` to `2025-12-31`

## Core tables

- `retail_core.stores`
  - One row per store location.
  - Keys: `store_id`.
- `retail_core.brands`
  - Brand reference list used by products and preferences.
  - Keys: `brand_id`.
- `retail_core.products`
  - Product catalog records with category, color, size, and list price.
  - Keys: `product_id`.
- `retail_core.customers`
  - Customer identity and segmentation columns.
  - Includes `email`, `tier`, `preferred_store_id`, `stylist_notes`, `lifetime_value_band`.
- `retail_core.customer_preferences`
  - Array preferences for sizes, colors, brands, and shopping occasions.
- `retail_core.saved_items`
  - Customer saved-item events.

## Sales tables

- `retail_sales.transactions`
  - One row per Q4 transaction event.
  - Contains totals (`gross_amount`, `discount_amount`, `net_amount`).
- `retail_sales.transaction_items`
  - Line items linked to transactions.
  - Contains quantity, unit price, and line totals.
- `retail_sales.returns`
  - Return events linked to transaction items.

## Analytics structures

- `retail_analytics.customer_recent_purchases` (materialized view)
- `retail_analytics.customer_saved_items_summary` (materialized view)
- `retail_analytics.customer_return_history_summary` (materialized view)
- `retail_analytics.customer_360` (view with required GPT fields)

## Expected row-count ranges

These ranges are useful for sanity checks after import:

- `stores`: exactly configured store count (default `1,100`)
- `brands`: exactly `42`
- `products`: exactly configured product count (default `120,000`)
- `customers`: exactly configured customer count (default `750,000`)
- `customer_preferences`: equals customer count
- `saved_items`: typically 20% to 60% of customer count (multi-row; often ~1M to 3M with defaults)
- `transactions`: exactly configured transaction count (default `10,000,000`)
- `transaction_items`: typically 1.5x to 2.2x transactions
- `returns`: typically 5% to 18% of transaction items

## Q4 integrity expectation

- All `retail_sales.transactions.transaction_ts` should be within `2025-10-01` through `2025-12-31`.
