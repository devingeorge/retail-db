\set ON_ERROR_STOP on

\echo ===== Row Count Checks =====
SELECT 'stores' AS table_name, COUNT(*) AS row_count FROM retail_core.stores
UNION ALL
SELECT 'brands', COUNT(*) FROM retail_core.brands
UNION ALL
SELECT 'products', COUNT(*) FROM retail_core.products
UNION ALL
SELECT 'customers', COUNT(*) FROM retail_core.customers
UNION ALL
SELECT 'customer_preferences', COUNT(*) FROM retail_core.customer_preferences
UNION ALL
SELECT 'saved_items', COUNT(*) FROM retail_core.saved_items
UNION ALL
SELECT 'transactions', COUNT(*) FROM retail_sales.transactions
UNION ALL
SELECT 'transaction_items', COUNT(*) FROM retail_sales.transaction_items
UNION ALL
SELECT 'returns', COUNT(*) FROM retail_sales.returns;

\echo ===== Key Uniqueness Checks =====
SELECT 'customers.customer_id duplicates' AS check_name, COUNT(*) AS duplicate_keys
FROM (
    SELECT customer_id
    FROM retail_core.customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) d
UNION ALL
SELECT 'customers.loyalty_id duplicates', COUNT(*)
FROM (
    SELECT loyalty_id
    FROM retail_core.customers
    GROUP BY loyalty_id
    HAVING COUNT(*) > 1
) d
UNION ALL
SELECT 'customers.email duplicates', COUNT(*)
FROM (
    SELECT email
    FROM retail_core.customers
    GROUP BY email
    HAVING COUNT(*) > 1
) d
UNION ALL
SELECT 'transactions.transaction_id duplicates', COUNT(*)
FROM (
    SELECT transaction_id
    FROM retail_sales.transactions
    GROUP BY transaction_id
    HAVING COUNT(*) > 1
) d;

\echo ===== Q4 Date Integrity =====
SELECT
    MIN(transaction_ts) AS min_transaction_ts,
    MAX(transaction_ts) AS max_transaction_ts,
    SUM(CASE WHEN transaction_ts::date < DATE '2025-10-01' OR transaction_ts::date > DATE '2025-12-31' THEN 1 ELSE 0 END) AS out_of_q4_rows
FROM retail_sales.transactions;

\echo ===== Referential Integrity Spot Checks =====
SELECT
    SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS orphan_transactions_customers
FROM retail_sales.transactions t
LEFT JOIN retail_core.customers c ON c.customer_id = t.customer_id;

SELECT
    SUM(CASE WHEN t.transaction_id IS NULL THEN 1 ELSE 0 END) AS orphan_items_transactions
FROM retail_sales.transaction_items i
LEFT JOIN retail_sales.transactions t ON t.transaction_id = i.transaction_id;

SELECT
    SUM(CASE WHEN i.transaction_item_id IS NULL THEN 1 ELSE 0 END) AS orphan_returns_items
FROM retail_sales.returns r
LEFT JOIN retail_sales.transaction_items i ON i.transaction_item_id = r.transaction_item_id;

\echo ===== Customer 360 Field Coverage =====
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN email IS NULL OR email = '' THEN 1 ELSE 0 END) AS missing_email,
    SUM(CASE WHEN preferred_sizes IS NULL OR array_length(preferred_sizes, 1) = 0 THEN 1 ELSE 0 END) AS missing_preferred_sizes,
    SUM(CASE WHEN preferred_colors IS NULL OR array_length(preferred_colors, 1) = 0 THEN 1 ELSE 0 END) AS missing_preferred_colors,
    SUM(CASE WHEN preferred_brands IS NULL OR array_length(preferred_brands, 1) = 0 THEN 1 ELSE 0 END) AS missing_preferred_brands,
    SUM(CASE WHEN shopping_occasions IS NULL OR array_length(shopping_occasions, 1) = 0 THEN 1 ELSE 0 END) AS missing_shopping_occasions,
    SUM(CASE WHEN lifetime_value_band IS NULL THEN 1 ELSE 0 END) AS missing_lifetime_value_band
FROM retail_analytics.customer_360;
