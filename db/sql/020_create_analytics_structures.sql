DROP MATERIALIZED VIEW IF EXISTS retail_analytics.customer_recent_purchases;
CREATE MATERIALIZED VIEW retail_analytics.customer_recent_purchases AS
WITH ranked AS (
    SELECT
        t.customer_id,
        t.transaction_id,
        t.transaction_ts,
        t.net_amount,
        ROW_NUMBER() OVER (
            PARTITION BY t.customer_id
            ORDER BY t.transaction_ts DESC, t.transaction_id DESC
        ) AS rn
    FROM retail_sales.transactions t
)
SELECT
    customer_id,
    MAX(transaction_ts) AS last_purchase_ts,
    JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'transaction_id', transaction_id,
            'transaction_ts', transaction_ts,
            'net_amount', net_amount
        )
        ORDER BY transaction_ts DESC, transaction_id DESC
    ) FILTER (WHERE rn <= 5) AS recent_purchases
FROM ranked
GROUP BY customer_id;

DROP MATERIALIZED VIEW IF EXISTS retail_analytics.customer_saved_items_summary;
CREATE MATERIALIZED VIEW retail_analytics.customer_saved_items_summary AS
SELECT
    s.customer_id,
    COUNT(*) AS saved_item_count,
    JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'product_id', s.product_id,
            'saved_at', s.saved_at,
            'product_name', p.product_name,
            'category', p.category,
            'color', p.color,
            'size_code', p.size_code
        )
        ORDER BY s.saved_at DESC
    ) AS saved_items
FROM retail_core.saved_items s
JOIN retail_core.products p ON p.product_id = s.product_id
GROUP BY s.customer_id;

DROP MATERIALIZED VIEW IF EXISTS retail_analytics.customer_return_history_summary;
CREATE MATERIALIZED VIEW retail_analytics.customer_return_history_summary AS
SELECT
    r.customer_id,
    COUNT(*) AS total_returns,
    ROUND(AVG(r.refund_amount), 2) AS avg_refund_amount,
    ROUND(SUM(r.refund_amount), 2) AS total_refund_amount,
    JSONB_BUILD_OBJECT(
        'total_returns', COUNT(*),
        'avg_refund_amount', ROUND(AVG(r.refund_amount), 2),
        'total_refund_amount', ROUND(SUM(r.refund_amount), 2),
        'top_reason', MODE() WITHIN GROUP (ORDER BY r.reason_code)
    ) AS return_history_summary
FROM retail_sales.returns r
GROUP BY r.customer_id;

DROP VIEW IF EXISTS retail_analytics.customer_360;
CREATE VIEW retail_analytics.customer_360 AS
SELECT
    c.customer_id,
    c.loyalty_id,
    c.first_name,
    c.last_name,
    c.tier,
    c.preferred_store_id,
    p.preferred_sizes,
    p.preferred_colors,
    p.preferred_brands,
    p.shopping_occasions,
    COALESCE(rp.recent_purchases, '[]'::JSONB) AS recent_purchases,
    COALESCE(si.saved_items, '[]'::JSONB) AS saved_items,
    COALESCE(
        rh.return_history_summary,
        JSONB_BUILD_OBJECT(
            'total_returns', 0,
            'avg_refund_amount', 0,
            'total_refund_amount', 0,
            'top_reason', NULL
        )
    ) AS return_history_summary,
    c.stylist_notes,
    c.lifetime_value_band
FROM retail_core.customers c
LEFT JOIN retail_core.customer_preferences p ON p.customer_id = c.customer_id
LEFT JOIN retail_analytics.customer_recent_purchases rp ON rp.customer_id = c.customer_id
LEFT JOIN retail_analytics.customer_saved_items_summary si ON si.customer_id = c.customer_id
LEFT JOIN retail_analytics.customer_return_history_summary rh ON rh.customer_id = c.customer_id;

CREATE INDEX IF NOT EXISTS idx_transactions_customer_ts
    ON retail_sales.transactions(customer_id, transaction_ts DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_q4_ts
    ON retail_sales.transactions(transaction_ts);
CREATE INDEX IF NOT EXISTS idx_transaction_items_transaction_id
    ON retail_sales.transaction_items(transaction_id);
CREATE INDEX IF NOT EXISTS idx_returns_customer_ts
    ON retail_sales.returns(customer_id, return_ts DESC);
CREATE INDEX IF NOT EXISTS idx_saved_items_customer_ts
    ON retail_core.saved_items(customer_id, saved_at DESC);
