DROP SCHEMA IF EXISTS retail_demo CASCADE;
DROP SCHEMA IF EXISTS retail_usecases CASCADE;
DROP SCHEMA IF EXISTS retail_sales CASCADE;
DROP SCHEMA IF EXISTS retail_analytics CASCADE;
DROP SCHEMA IF EXISTS retail_core CASCADE;
DROP SCHEMA IF EXISTS "ORDERS" CASCADE;

\i db/sql/080_create_minimal_demo_tables.sql
\i db/sql/081_seed_minimal_demo_data.sql
