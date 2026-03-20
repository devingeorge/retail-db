CREATE SCHEMA IF NOT EXISTS retail_usecases;

CREATE TABLE IF NOT EXISTS retail_usecases.styles (
    style_id TEXT PRIMARY KEY,
    style_name TEXT NOT NULL,
    category TEXT NOT NULL,
    season TEXT NOT NULL,
    planned_cc_count INTEGER NOT NULL,
    core_vs_fashion TEXT NOT NULL CHECK (core_vs_fashion IN ('core', 'fashion')),
    strategic_priority TEXT NOT NULL CHECK (strategic_priority IN ('maintain', 'grow', 'optimize'))
);

CREATE TABLE IF NOT EXISTS retail_usecases.skus (
    sku TEXT PRIMARY KEY,
    style_id TEXT NOT NULL REFERENCES retail_usecases.styles(style_id),
    color_name TEXT NOT NULL,
    size TEXT NOT NULL,
    msrp NUMERIC(10, 2) NOT NULL,
    cost NUMERIC(10, 2) NOT NULL,
    substitute_style_id TEXT REFERENCES retail_usecases.styles(style_id),
    trade_up_style_id TEXT REFERENCES retail_usecases.styles(style_id)
);

CREATE TABLE IF NOT EXISTS retail_usecases.inventory (
    store_id INTEGER NOT NULL,
    store_name TEXT NOT NULL,
    region TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES retail_usecases.skus(sku),
    on_hand_units INTEGER NOT NULL,
    available_for_transfer BOOLEAN NOT NULL,
    available_online_dc INTEGER NOT NULL,
    PRIMARY KEY (store_id, sku)
);

CREATE TABLE IF NOT EXISTS retail_usecases.sales_summary (
    period TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES retail_usecases.skus(sku),
    style_id TEXT NOT NULL REFERENCES retail_usecases.styles(style_id),
    units_sold INTEGER NOT NULL,
    net_sales NUMERIC(12, 2) NOT NULL,
    gross_margin_pct NUMERIC(5, 2) NOT NULL,
    sell_through_pct NUMERIC(5, 2) NOT NULL,
    markdown_rate NUMERIC(5, 2) NOT NULL,
    return_rate NUMERIC(5, 2) NOT NULL,
    store_count INTEGER NOT NULL,
    PRIMARY KEY (period, sku)
);

CREATE TABLE IF NOT EXISTS retail_usecases.customer_profiles (
    customer_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('Bronze', 'Silver', 'Gold', 'Platinum')),
    preferred_sizes TEXT[] NOT NULL,
    preferred_colors TEXT[] NOT NULL,
    favorite_categories TEXT[] NOT NULL,
    recent_purchases JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_usecases.style_relationships (
    from_style_id TEXT NOT NULL REFERENCES retail_usecases.styles(style_id),
    to_style_id TEXT NOT NULL REFERENCES retail_usecases.styles(style_id),
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('cross_sell')),
    rationale TEXT,
    priority_rank INTEGER NOT NULL DEFAULT 1 CHECK (priority_rank > 0),
    PRIMARY KEY (from_style_id, to_style_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_usecases_inventory_sku ON retail_usecases.inventory(sku);
CREATE INDEX IF NOT EXISTS idx_usecases_sales_summary_sku ON retail_usecases.sales_summary(sku);
CREATE INDEX IF NOT EXISTS idx_usecases_sales_summary_style ON retail_usecases.sales_summary(style_id);
CREATE INDEX IF NOT EXISTS idx_usecases_style_relationships_from ON retail_usecases.style_relationships(from_style_id);
