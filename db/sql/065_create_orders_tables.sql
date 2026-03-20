CREATE TABLE IF NOT EXISTS "ORDERS".orders (
    order_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES retail_core.customers(customer_id),
    store_id INTEGER NOT NULL REFERENCES retail_core.stores(store_id),
    order_status TEXT NOT NULL CHECK (order_status IN ('pending', 'placed', 'fulfilled', 'cancelled')),
    order_source TEXT NOT NULL DEFAULT 'gpt_action',
    associate_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "ORDERS".order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES "ORDERS".orders(order_id) ON DELETE CASCADE,
    sku TEXT NOT NULL REFERENCES retail_usecases.skus(sku),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

CREATE INDEX IF NOT EXISTS orders_customer_created_at_idx
    ON "ORDERS".orders (customer_id, created_at DESC);

CREATE INDEX IF NOT EXISTS order_items_order_id_idx
    ON "ORDERS".order_items (order_id);

CREATE INDEX IF NOT EXISTS order_items_sku_idx
    ON "ORDERS".order_items (sku);
