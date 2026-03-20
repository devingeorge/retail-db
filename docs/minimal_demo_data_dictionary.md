# Minimal Demo Data Dictionary

This dictionary describes the intentionally small unified demo model in schema `retail_demo`.

## Tables

### `retail_demo.products`

SKU-level product catalog with style-level identifiers.

- `product_id` (TEXT, PK): product record identifier for GPT lookups.
- `style_id` (TEXT): shared style identifier across related SKUs.
- `sku_id` (TEXT, UNIQUE): concrete purchasable variant.
- `product_name` (TEXT): real-sounding customer-facing product name.
- `category` / `subcategory` (TEXT): reporting and filtering dimensions.
- `brand` (TEXT): brand family.
- `color` / `size` (TEXT): variant attributes.
- `season` (TEXT): season grouping.
- `msrp` / `cost` (NUMERIC): price and cost.
- `description` (TEXT): concise selling copy.
- `image_url` (TEXT): externally hosted product image.
- `silhouette` / `occasion` / `material` (TEXT): recommendation attributes.
- `status` (TEXT): `active` or `inactive`.

### `retail_demo.stores`

Minimal location network for demo flows.

- `store_id` (INTEGER, PK)
- `store_name` (TEXT)
- `city` / `state` / `region` (TEXT)
- `store_type` (TEXT)

### `retail_demo.inventory`

Store-level SKU availability.

- `store_id` (FK to stores)
- `sku_id` (FK to products)
- `on_hand_qty` (INTEGER)
- `reserved_qty` (INTEGER)
- `available_qty` (INTEGER, constrained to `on_hand_qty - reserved_qty`)
- `in_transit_qty` (INTEGER)
- `last_updated` (TIMESTAMPTZ)

### `retail_demo.product_relationships`

Explicit recommendation links to avoid complex inference.

- `source_product_id` (FK to products)
- `related_product_id` (FK to products)
- `relationship_type` (`alternative` or `complementary`)
- `relationship_reason` (TEXT)

### `retail_demo.orders`

Order header for cross-store fulfillment.

- `order_id` (TEXT, PK)
- `customer_id` (TEXT)
- `order_date` (TIMESTAMPTZ)
- `order_status` (`placed`, `processing`, `shipped`, `delivered`, `cancelled`)
- `fulfillment_store_id` (FK to stores)
- `destination_store_id` (nullable FK to stores)
- `ship_to_city` (nullable TEXT)
- `shipping_method` (`standard`, `expedited`, `overnight`, `store_pickup`)
- `estimated_delivery_days` (INTEGER)
- `estimated_delivery_date` (DATE)

### `retail_demo.order_line_items`

Order item detail.

- `order_id` (FK to orders)
- `sku_id` (FK to products)
- `quantity` (INTEGER)
- `unit_price` (NUMERIC)

### `retail_demo.weekly_performance_summary`

Compact style-level performance signals by store/week.

- `week_start_date` (DATE)
- `store_id` (FK to stores)
- `style_id` (TEXT)
- `units_sold` (INTEGER)
- `net_sales` (NUMERIC)
- `gross_margin` (NUMERIC)
- `markdown_rate` (NUMERIC percent)
- `sell_through_pct` (NUMERIC percent)
- `weeks_of_supply` (NUMERIC)

## Embedded Demo Story

- Portland (`store_id=101`) is out of stock on the target dress variant.
- Boston (`store_id=102`) and Philadelphia (`store_id=103`) have available inventory for that exact variant.
- Portland has an alternative dress and complementary shoes in stock.
- Weekly summary data supports a planning narrative: strong Portland demand with Boston/Philadelphia over-allocation on the target style.
