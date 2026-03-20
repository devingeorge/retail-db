CREATE SCHEMA IF NOT EXISTS retail_demo;

CREATE TABLE IF NOT EXISTS retail_demo.products (
    product_id TEXT PRIMARY KEY,
    style_id TEXT NOT NULL,
    sku_id TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    brand TEXT NOT NULL,
    color TEXT NOT NULL,
    size TEXT NOT NULL,
    season TEXT NOT NULL,
    msrp NUMERIC(10, 2) NOT NULL,
    cost NUMERIC(10, 2) NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT NOT NULL,
    silhouette TEXT NOT NULL,
    occasion TEXT NOT NULL,
    material TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS retail_demo.stores (
    store_id INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    region TEXT NOT NULL,
    store_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_demo.inventory (
    store_id INTEGER NOT NULL REFERENCES retail_demo.stores(store_id),
    sku_id TEXT NOT NULL REFERENCES retail_demo.products(sku_id),
    on_hand_qty INTEGER NOT NULL CHECK (on_hand_qty >= 0),
    reserved_qty INTEGER NOT NULL CHECK (reserved_qty >= 0),
    available_qty INTEGER NOT NULL CHECK (available_qty >= 0),
    in_transit_qty INTEGER NOT NULL CHECK (in_transit_qty >= 0),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (store_id, sku_id),
    CHECK (available_qty = on_hand_qty - reserved_qty)
);

CREATE TABLE IF NOT EXISTS retail_demo.product_relationships (
    source_product_id TEXT NOT NULL REFERENCES retail_demo.products(product_id),
    related_product_id TEXT NOT NULL REFERENCES retail_demo.products(product_id),
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('alternative', 'complementary')),
    relationship_reason TEXT NOT NULL,
    PRIMARY KEY (source_product_id, related_product_id, relationship_type),
    CHECK (source_product_id <> related_product_id)
);

CREATE TABLE IF NOT EXISTS retail_demo.orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    order_status TEXT NOT NULL CHECK (order_status IN ('placed', 'processing', 'shipped', 'delivered', 'cancelled')),
    fulfillment_store_id INTEGER NOT NULL REFERENCES retail_demo.stores(store_id),
    destination_store_id INTEGER REFERENCES retail_demo.stores(store_id),
    ship_to_city TEXT,
    shipping_method TEXT NOT NULL CHECK (shipping_method IN ('standard', 'expedited', 'overnight', 'store_pickup')),
    estimated_delivery_days INTEGER NOT NULL CHECK (estimated_delivery_days >= 0),
    estimated_delivery_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_demo.order_line_items (
    order_id TEXT NOT NULL REFERENCES retail_demo.orders(order_id) ON DELETE CASCADE,
    sku_id TEXT NOT NULL REFERENCES retail_demo.products(sku_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, sku_id)
);

CREATE TABLE IF NOT EXISTS retail_demo.weekly_performance_summary (
    week_start_date DATE NOT NULL,
    store_id INTEGER NOT NULL REFERENCES retail_demo.stores(store_id),
    style_id TEXT NOT NULL,
    units_sold INTEGER NOT NULL CHECK (units_sold >= 0),
    net_sales NUMERIC(12, 2) NOT NULL CHECK (net_sales >= 0),
    gross_margin NUMERIC(12, 2) NOT NULL,
    markdown_rate NUMERIC(5, 2) NOT NULL CHECK (markdown_rate >= 0 AND markdown_rate <= 100),
    sell_through_pct NUMERIC(5, 2) NOT NULL CHECK (sell_through_pct >= 0 AND sell_through_pct <= 100),
    weeks_of_supply NUMERIC(6, 2) NOT NULL CHECK (weeks_of_supply >= 0),
    PRIMARY KEY (week_start_date, store_id, style_id)
);

CREATE INDEX IF NOT EXISTS idx_demo_products_style ON retail_demo.products(style_id);
CREATE INDEX IF NOT EXISTS idx_demo_products_category ON retail_demo.products(category);
CREATE INDEX IF NOT EXISTS idx_demo_inventory_sku ON retail_demo.inventory(sku_id);
CREATE INDEX IF NOT EXISTS idx_demo_relationships_source ON retail_demo.product_relationships(source_product_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_demo_perf_style_store ON retail_demo.weekly_performance_summary(style_id, store_id, week_start_date);
