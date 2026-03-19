CREATE SCHEMA IF NOT EXISTS retail_core;
CREATE SCHEMA IF NOT EXISTS retail_sales;
CREATE SCHEMA IF NOT EXISTS retail_analytics;

CREATE TABLE IF NOT EXISTS retail_core.stores (
    store_id INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    region TEXT NOT NULL,
    state_code TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_core.brands (
    brand_id INTEGER PRIMARY KEY,
    brand_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS retail_core.products (
    product_id BIGINT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand_id INTEGER NOT NULL REFERENCES retail_core.brands(brand_id),
    color TEXT NOT NULL,
    size_code TEXT NOT NULL,
    list_price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_core.customers (
    customer_id BIGINT PRIMARY KEY,
    loyalty_id TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('Bronze', 'Silver', 'Gold', 'Platinum')),
    preferred_store_id INTEGER REFERENCES retail_core.stores(store_id),
    stylist_notes TEXT NOT NULL,
    lifetime_value_band TEXT NOT NULL CHECK (lifetime_value_band IN ('Low', 'Medium', 'High', 'VIP')),
    created_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_core.customer_preferences (
    customer_id BIGINT PRIMARY KEY REFERENCES retail_core.customers(customer_id),
    preferred_sizes TEXT[] NOT NULL,
    preferred_colors TEXT[] NOT NULL,
    preferred_brands TEXT[] NOT NULL,
    shopping_occasions TEXT[] NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS retail_core.saved_items (
    saved_item_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES retail_core.customers(customer_id),
    product_id BIGINT NOT NULL REFERENCES retail_core.products(product_id),
    saved_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_sales.transactions (
    transaction_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES retail_core.customers(customer_id),
    store_id INTEGER NOT NULL REFERENCES retail_core.stores(store_id),
    transaction_ts TIMESTAMPTZ NOT NULL,
    sales_channel TEXT NOT NULL CHECK (sales_channel IN ('in_store', 'online', 'mobile')),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('card', 'cash', 'wallet', 'gift_card')),
    gross_amount NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) NOT NULL,
    net_amount NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_sales.transaction_items (
    transaction_item_id BIGINT PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES retail_sales.transactions(transaction_id),
    product_id BIGINT NOT NULL REFERENCES retail_core.products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) NOT NULL,
    line_total NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_sales.returns (
    return_id BIGINT PRIMARY KEY,
    transaction_item_id BIGINT NOT NULL REFERENCES retail_sales.transaction_items(transaction_item_id),
    customer_id BIGINT NOT NULL REFERENCES retail_core.customers(customer_id),
    return_ts TIMESTAMPTZ NOT NULL,
    reason_code TEXT NOT NULL CHECK (
        reason_code IN (
            'size_issue',
            'quality_issue',
            'damaged_in_shipping',
            'late_delivery',
            'changed_mind',
            'wrong_item'
        )
    ),
    refund_amount NUMERIC(10, 2) NOT NULL
);
