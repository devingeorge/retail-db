DROP INDEX IF EXISTS retail_analytics.idx_customer_recent_purchases_customer_id;
DROP INDEX IF EXISTS retail_analytics.idx_customer_saved_items_summary_customer_id;
DROP INDEX IF EXISTS retail_analytics.idx_customer_return_history_summary_customer_id;

REFRESH MATERIALIZED VIEW retail_analytics.customer_recent_purchases;
REFRESH MATERIALIZED VIEW retail_analytics.customer_saved_items_summary;
REFRESH MATERIALIZED VIEW retail_analytics.customer_return_history_summary;

CREATE INDEX IF NOT EXISTS idx_customer_recent_purchases_customer_id
    ON retail_analytics.customer_recent_purchases(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_saved_items_summary_customer_id
    ON retail_analytics.customer_saved_items_summary(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_return_history_summary_customer_id
    ON retail_analytics.customer_return_history_summary(customer_id);

ANALYZE retail_core.stores;
ANALYZE retail_core.brands;
ANALYZE retail_core.products;
ANALYZE retail_core.customers;
ANALYZE retail_core.customer_preferences;
ANALYZE retail_core.saved_items;
ANALYZE retail_sales.transactions;
ANALYZE retail_sales.transaction_items;
ANALYZE retail_sales.returns;
ANALYZE retail_analytics.customer_recent_purchases;
ANALYZE retail_analytics.customer_saved_items_summary;
ANALYZE retail_analytics.customer_return_history_summary;
