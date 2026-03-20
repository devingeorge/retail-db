INSERT INTO retail_demo.stores (store_id, store_name, city, state, region, store_type)
VALUES
    (101, 'Portland Flagship', 'Portland', 'ME', 'Northeast', 'Flagship'),
    (102, 'Boston Boylston', 'Boston', 'MA', 'Northeast', 'Urban'),
    (103, 'Philadelphia Center City', 'Philadelphia', 'PA', 'Northeast', 'Urban')
ON CONFLICT (store_id) DO UPDATE
SET
    store_name = EXCLUDED.store_name,
    city = EXCLUDED.city,
    state = EXCLUDED.state,
    region = EXCLUDED.region,
    store_type = EXCLUDED.store_type;

INSERT INTO retail_demo.products (
    product_id, style_id, sku_id, product_name, category, subcategory, brand,
    color, size, season, msrp, cost, description, image_url, silhouette,
    occasion, material, status
)
VALUES
    ('PRD-1001', 'STY-D001', 'SKU-D001-RSE-M', 'Harborlight Satin Midi Dress', 'Dresses', 'Midi', 'Northline Atelier', 'Rose', 'M', 'Spring-Summer', 168.00, 62.00, 'Fluid satin midi dress with soft drape and waist definition.', 'https://images.unsplash.com/photo-1591369822096-ffd140ec948f?auto=format&fit=crop&w=1200&q=80', 'Fit-and-flare', 'Wedding Guest', 'Satin', 'active'),
    ('PRD-1002', 'STY-D001', 'SKU-D001-RSE-S', 'Harborlight Satin Midi Dress', 'Dresses', 'Midi', 'Northline Atelier', 'Rose', 'S', 'Spring-Summer', 168.00, 62.00, 'Fluid satin midi dress with soft drape and waist definition.', 'https://images.unsplash.com/photo-1591369822096-ffd140ec948f?auto=format&fit=crop&w=1200&q=80', 'Fit-and-flare', 'Wedding Guest', 'Satin', 'active'),
    ('PRD-2001', 'STY-D002', 'SKU-D002-NVY-M', 'Crescent Pleat Wrap Dress', 'Dresses', 'Wrap', 'Northline Atelier', 'Navy', 'M', 'Spring-Summer', 142.00, 54.00, 'Pleated wrap dress with adjustable waist tie for all-day comfort.', 'https://images.unsplash.com/photo-1495385794356-15371f348c31?auto=format&fit=crop&w=1200&q=80', 'Wrap', 'Wedding Guest', 'Recycled Polyester', 'active'),
    ('PRD-2002', 'STY-D002', 'SKU-D002-NVY-S', 'Crescent Pleat Wrap Dress', 'Dresses', 'Wrap', 'Northline Atelier', 'Navy', 'S', 'Spring-Summer', 142.00, 54.00, 'Pleated wrap dress with adjustable waist tie for all-day comfort.', 'https://images.unsplash.com/photo-1495385794356-15371f348c31?auto=format&fit=crop&w=1200&q=80', 'Wrap', 'Wedding Guest', 'Recycled Polyester', 'active'),
    ('PRD-2101', 'STY-D003', 'SKU-D003-SGE-M', 'Alder Knit Column Dress', 'Dresses', 'Column', 'Northline Atelier', 'Sage', 'M', 'Spring-Summer', 128.00, 46.00, 'Soft knit column silhouette with modern square neckline.', 'https://images.unsplash.com/photo-1464863979621-258859e62245?auto=format&fit=crop&w=1200&q=80', 'Column', 'Day Event', 'Viscose Blend', 'active'),
    ('PRD-3001', 'STY-S001', 'SKU-S001-WHT-8', 'Marin Court Sneaker', 'Shoes', 'Sneakers', 'Harbor & Pine', 'White', '8', 'Spring-Summer', 110.00, 40.00, 'Clean leather court sneaker with cushioned insole.', 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=1200&q=80', 'Low-top', 'Wedding Guest', 'Leather', 'active'),
    ('PRD-3002', 'STY-S001', 'SKU-S001-WHT-9', 'Marin Court Sneaker', 'Shoes', 'Sneakers', 'Harbor & Pine', 'White', '9', 'Spring-Summer', 110.00, 40.00, 'Clean leather court sneaker with cushioned insole.', 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=1200&q=80', 'Low-top', 'Wedding Guest', 'Leather', 'active'),
    ('PRD-3101', 'STY-S002', 'SKU-S002-NUD-8', 'Beacon Slingback Heel', 'Shoes', 'Heels', 'Harbor & Pine', 'Nude', '8', 'Spring-Summer', 124.00, 45.00, 'Pointed slingback heel designed for occasion wear.', 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=1200&q=80', 'Slingback', 'Wedding Guest', 'Faux Leather', 'active'),
    ('PRD-3201', 'STY-S003', 'SKU-S003-BLK-8', 'Harbor Strap Sandal', 'Shoes', 'Sandals', 'Harbor & Pine', 'Black', '8', 'Spring-Summer', 98.00, 36.00, 'Minimal strap sandal with low block heel.', 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=1200&q=80', 'Strappy', 'Day Event', 'Leather', 'active')
ON CONFLICT (product_id) DO UPDATE
SET
    style_id = EXCLUDED.style_id,
    sku_id = EXCLUDED.sku_id,
    product_name = EXCLUDED.product_name,
    category = EXCLUDED.category,
    subcategory = EXCLUDED.subcategory,
    brand = EXCLUDED.brand,
    color = EXCLUDED.color,
    size = EXCLUDED.size,
    season = EXCLUDED.season,
    msrp = EXCLUDED.msrp,
    cost = EXCLUDED.cost,
    description = EXCLUDED.description,
    image_url = EXCLUDED.image_url,
    silhouette = EXCLUDED.silhouette,
    occasion = EXCLUDED.occasion,
    material = EXCLUDED.material,
    status = EXCLUDED.status;

INSERT INTO retail_demo.inventory (
    store_id, sku_id, on_hand_qty, reserved_qty, available_qty, in_transit_qty, last_updated
)
VALUES
    (101, 'SKU-D001-RSE-M', 0, 0, 0, 2, NOW()),
    (102, 'SKU-D001-RSE-M', 6, 1, 5, 0, NOW()),
    (103, 'SKU-D001-RSE-M', 4, 0, 4, 0, NOW()),
    (101, 'SKU-D002-NVY-M', 5, 0, 5, 0, NOW()),
    (102, 'SKU-D002-NVY-M', 2, 0, 2, 0, NOW()),
    (103, 'SKU-D002-NVY-M', 1, 0, 1, 0, NOW()),
    (101, 'SKU-D003-SGE-M', 3, 0, 3, 0, NOW()),
    (102, 'SKU-D003-SGE-M', 2, 0, 2, 0, NOW()),
    (103, 'SKU-D003-SGE-M', 2, 0, 2, 0, NOW()),
    (101, 'SKU-S001-WHT-8', 7, 0, 7, 0, NOW()),
    (102, 'SKU-S001-WHT-8', 8, 0, 8, 0, NOW()),
    (103, 'SKU-S001-WHT-8', 5, 0, 5, 0, NOW()),
    (101, 'SKU-S001-WHT-9', 4, 0, 4, 0, NOW()),
    (102, 'SKU-S001-WHT-9', 3, 0, 3, 0, NOW()),
    (101, 'SKU-S002-NUD-8', 6, 0, 6, 0, NOW()),
    (102, 'SKU-S002-NUD-8', 2, 0, 2, 0, NOW()),
    (101, 'SKU-S003-BLK-8', 5, 0, 5, 0, NOW())
ON CONFLICT (store_id, sku_id) DO UPDATE
SET
    on_hand_qty = EXCLUDED.on_hand_qty,
    reserved_qty = EXCLUDED.reserved_qty,
    available_qty = EXCLUDED.available_qty,
    in_transit_qty = EXCLUDED.in_transit_qty,
    last_updated = EXCLUDED.last_updated;

INSERT INTO retail_demo.product_relationships (
    source_product_id, related_product_id, relationship_type, relationship_reason
)
VALUES
    ('PRD-1001', 'PRD-2001', 'alternative', 'Similar wedding-guest silhouette with in-stock size M in Portland.'),
    ('PRD-1001', 'PRD-3101', 'complementary', 'Neutral slingback complements the rose satin color palette.'),
    ('PRD-1001', 'PRD-3001', 'complementary', 'White sneaker offers a comfort-first modern wedding look.'),
    ('PRD-2001', 'PRD-3001', 'complementary', 'Clean white sneaker balances navy wrap styling.'),
    ('PRD-2001', 'PRD-3101', 'complementary', 'Slingback heel elevates navy wrap dress for evening events.')
ON CONFLICT (source_product_id, related_product_id, relationship_type) DO UPDATE
SET relationship_reason = EXCLUDED.relationship_reason;

INSERT INTO retail_demo.orders (
    order_id, customer_id, order_date, order_status, fulfillment_store_id, destination_store_id,
    ship_to_city, shipping_method, estimated_delivery_days, estimated_delivery_date
)
VALUES
    ('ORD-9001', 'CUST-LEAH-001', NOW() - INTERVAL '1 day', 'placed', 102, 101, 'Portland', 'standard', 3, CURRENT_DATE + 2)
ON CONFLICT (order_id) DO UPDATE
SET
    customer_id = EXCLUDED.customer_id,
    order_date = EXCLUDED.order_date,
    order_status = EXCLUDED.order_status,
    fulfillment_store_id = EXCLUDED.fulfillment_store_id,
    destination_store_id = EXCLUDED.destination_store_id,
    ship_to_city = EXCLUDED.ship_to_city,
    shipping_method = EXCLUDED.shipping_method,
    estimated_delivery_days = EXCLUDED.estimated_delivery_days,
    estimated_delivery_date = EXCLUDED.estimated_delivery_date;

INSERT INTO retail_demo.order_line_items (order_id, sku_id, quantity, unit_price)
VALUES
    ('ORD-9001', 'SKU-D001-RSE-M', 1, 168.00)
ON CONFLICT (order_id, sku_id) DO UPDATE
SET
    quantity = EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price;

INSERT INTO retail_demo.weekly_performance_summary (
    week_start_date, store_id, style_id, units_sold, net_sales, gross_margin, markdown_rate, sell_through_pct, weeks_of_supply
)
VALUES
    ('2026-01-05', 101, 'STY-D001', 6, 1008.00, 636.00, 2.00, 78.00, 0.20),
    ('2026-01-12', 101, 'STY-D001', 7, 1176.00, 742.00, 2.00, 81.00, 0.10),
    ('2026-01-19', 101, 'STY-D001', 5, 840.00, 530.00, 4.00, 74.00, 0.10),
    ('2026-01-26', 101, 'STY-D001', 4, 672.00, 425.00, 5.00, 69.00, 0.00),
    ('2026-01-05', 102, 'STY-D001', 2, 336.00, 212.00, 8.00, 34.00, 6.50),
    ('2026-01-12', 102, 'STY-D001', 2, 336.00, 212.00, 9.00, 31.00, 6.00),
    ('2026-01-19', 102, 'STY-D001', 1, 168.00, 106.00, 10.00, 20.00, 7.00),
    ('2026-01-26', 102, 'STY-D001', 1, 168.00, 106.00, 10.00, 18.00, 7.20),
    ('2026-01-05', 103, 'STY-D001', 2, 336.00, 212.00, 7.00, 38.00, 5.20),
    ('2026-01-12', 103, 'STY-D001', 1, 168.00, 106.00, 8.00, 27.00, 5.50),
    ('2026-01-19', 103, 'STY-D001', 1, 168.00, 106.00, 8.00, 24.00, 5.70),
    ('2026-01-26', 103, 'STY-D001', 1, 168.00, 106.00, 9.00, 21.00, 6.00),
    ('2026-01-05', 101, 'STY-D002', 3, 426.00, 264.00, 3.00, 62.00, 2.00),
    ('2026-01-12', 101, 'STY-D002', 4, 568.00, 352.00, 3.00, 66.00, 1.80),
    ('2026-01-19', 101, 'STY-D002', 2, 284.00, 176.00, 4.00, 54.00, 2.30),
    ('2026-01-26', 101, 'STY-D002', 3, 426.00, 264.00, 3.00, 58.00, 2.00),
    ('2026-01-05', 102, 'STY-D002', 2, 284.00, 176.00, 5.00, 43.00, 3.50),
    ('2026-01-12', 102, 'STY-D002', 1, 142.00, 88.00, 6.00, 33.00, 3.80),
    ('2026-01-19', 102, 'STY-D002', 1, 142.00, 88.00, 6.00, 30.00, 4.10),
    ('2026-01-26', 102, 'STY-D002', 1, 142.00, 88.00, 6.00, 28.00, 4.40),
    ('2026-01-05', 101, 'STY-S001', 5, 550.00, 350.00, 1.00, 72.00, 1.20),
    ('2026-01-12', 101, 'STY-S001', 4, 440.00, 280.00, 1.00, 70.00, 1.30),
    ('2026-01-19', 101, 'STY-S001', 4, 440.00, 280.00, 2.00, 68.00, 1.40),
    ('2026-01-26', 101, 'STY-S001', 3, 330.00, 210.00, 2.00, 64.00, 1.60)
ON CONFLICT (week_start_date, store_id, style_id) DO UPDATE
SET
    units_sold = EXCLUDED.units_sold,
    net_sales = EXCLUDED.net_sales,
    gross_margin = EXCLUDED.gross_margin,
    markdown_rate = EXCLUDED.markdown_rate,
    sell_through_pct = EXCLUDED.sell_through_pct,
    weeks_of_supply = EXCLUDED.weeks_of_supply;
