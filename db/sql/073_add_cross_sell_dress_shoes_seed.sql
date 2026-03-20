CREATE TABLE IF NOT EXISTS retail_usecases.style_relationships (
    from_style_id TEXT NOT NULL REFERENCES retail_usecases.styles(style_id),
    to_style_id TEXT NOT NULL REFERENCES retail_usecases.styles(style_id),
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('cross_sell')),
    rationale TEXT,
    priority_rank INTEGER NOT NULL DEFAULT 1 CHECK (priority_rank > 0),
    PRIMARY KEY (from_style_id, to_style_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_usecases_style_relationships_from
    ON retail_usecases.style_relationships(from_style_id);

INSERT INTO retail_usecases.styles (
    style_id,
    style_name,
    category,
    season,
    planned_cc_count,
    core_vs_fashion,
    strategic_priority
)
VALUES
    ('STY-1901', 'Evening Dress 1901', 'Dresses', 'Q4-2025', 5, 'fashion', 'grow'),
    ('STY-1902', 'Court Sneaker 1902', 'Sneakers', 'Q4-2025', 4, 'core', 'grow')
ON CONFLICT (style_id) DO UPDATE
SET
    style_name = EXCLUDED.style_name,
    category = EXCLUDED.category,
    season = EXCLUDED.season,
    planned_cc_count = EXCLUDED.planned_cc_count,
    core_vs_fashion = EXCLUDED.core_vs_fashion,
    strategic_priority = EXCLUDED.strategic_priority;

INSERT INTO retail_usecases.skus (
    sku,
    style_id,
    color_name,
    size,
    msrp,
    cost,
    substitute_style_id,
    trade_up_style_id
)
VALUES
    ('SKU-009901', 'STY-1901', 'Red', 'M', 189.00, 72.00, NULL, NULL),
    ('SKU-009902', 'STY-1902', 'White', '8', 129.00, 49.00, NULL, NULL)
ON CONFLICT (sku) DO UPDATE
SET
    style_id = EXCLUDED.style_id,
    color_name = EXCLUDED.color_name,
    size = EXCLUDED.size,
    msrp = EXCLUDED.msrp,
    cost = EXCLUDED.cost,
    substitute_style_id = EXCLUDED.substitute_style_id,
    trade_up_style_id = EXCLUDED.trade_up_style_id;

INSERT INTO retail_usecases.inventory (
    store_id,
    store_name,
    region,
    sku,
    on_hand_units,
    available_for_transfer,
    available_online_dc
)
VALUES
    (121, 'Store-121 (Northeast) - Portland, Maine Mall Road', 'Northeast', 'SKU-009901', 4, TRUE, 18),
    (121, 'Store-121 (Northeast) - Portland, Maine Mall Road', 'Northeast', 'SKU-009902', 9, TRUE, 24),
    (56, 'Boston - Boylston Street Location', 'Northeast', 'SKU-009902', 14, TRUE, 42)
ON CONFLICT (store_id, sku) DO UPDATE
SET
    store_name = EXCLUDED.store_name,
    region = EXCLUDED.region,
    on_hand_units = EXCLUDED.on_hand_units,
    available_for_transfer = EXCLUDED.available_for_transfer,
    available_online_dc = EXCLUDED.available_online_dc;

INSERT INTO retail_usecases.style_relationships (
    from_style_id,
    to_style_id,
    relationship_type,
    rationale,
    priority_rank
)
VALUES
    (
        'STY-1901',
        'STY-1902',
        'cross_sell',
        'Complete the look: pair the evening dress with clean white court sneakers.',
        1
    )
ON CONFLICT (from_style_id, to_style_id, relationship_type) DO UPDATE
SET
    rationale = EXCLUDED.rationale,
    priority_rank = EXCLUDED.priority_rank;
