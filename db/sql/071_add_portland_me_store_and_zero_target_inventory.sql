INSERT INTO retail_core.stores (
    store_id,
    store_name,
    region,
    state_code,
    city,
    street_address,
    postal_code
)
VALUES (
    121,
    'Store-121 (Northeast) - Portland, Maine Mall Road',
    'Northeast',
    'ME',
    'Portland',
    '500 Maine Mall Road',
    '04106'
)
ON CONFLICT (store_id) DO UPDATE
SET
    store_name = EXCLUDED.store_name,
    region = EXCLUDED.region,
    state_code = EXCLUDED.state_code,
    city = EXCLUDED.city,
    street_address = EXCLUDED.street_address,
    postal_code = EXCLUDED.postal_code;

WITH target_sku AS (
    SELECT sku
    FROM retail_usecases.skus
    WHERE style_id = 'STY-0128'
      AND LOWER(color_name) = 'red'
      AND size = 'M'
    LIMIT 1
)
INSERT INTO retail_usecases.inventory (
    store_id,
    store_name,
    region,
    sku,
    on_hand_units,
    available_for_transfer,
    available_online_dc
)
SELECT
    121,
    'Store-121 (Northeast) - Portland, Maine Mall Road',
    'Northeast',
    t.sku,
    0,
    FALSE,
    0
FROM target_sku t
ON CONFLICT (store_id, sku) DO UPDATE
SET
    store_name = EXCLUDED.store_name,
    region = EXCLUDED.region,
    on_hand_units = 0,
    available_for_transfer = FALSE,
    available_online_dc = 0;
