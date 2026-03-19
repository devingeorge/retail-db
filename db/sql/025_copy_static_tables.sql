\set ON_ERROR_STOP on

\echo Loading reference tables...
\copy retail_core.stores(store_id,store_name,region,state_code,city) FROM :'stores_csv' WITH (FORMAT csv, HEADER true)
\copy retail_core.brands(brand_id,brand_name) FROM :'brands_csv' WITH (FORMAT csv, HEADER true)
\copy retail_core.products(product_id,sku,product_name,category,brand_id,color,size_code,list_price) FROM :'products_csv' WITH (FORMAT csv, HEADER true)

\echo Loading core tables...
\copy retail_core.customers(customer_id,loyalty_id,first_name,last_name,tier,preferred_store_id,stylist_notes,lifetime_value_band,created_at) FROM :'customers_csv' WITH (FORMAT csv, HEADER true)
\copy retail_core.customer_preferences(customer_id,preferred_sizes,preferred_colors,preferred_brands,shopping_occasions,updated_at) FROM :'customer_preferences_csv' WITH (FORMAT csv, HEADER true)
\copy retail_core.saved_items(saved_item_id,customer_id,product_id,saved_at) FROM :'saved_items_csv' WITH (FORMAT csv, HEADER true)
