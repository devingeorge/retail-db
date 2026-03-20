ALTER TABLE retail_core.stores
ADD COLUMN IF NOT EXISTS street_address TEXT;

ALTER TABLE retail_core.stores
ADD COLUMN IF NOT EXISTS postal_code TEXT;

WITH region_city_map AS (
    SELECT
        s.store_id,
        s.region,
        CASE s.region
            WHEN 'Northeast' THEN
                (ARRAY['Boston','New York','Philadelphia','Providence','Hartford','Newark'])[(s.store_id % 6) + 1]
            WHEN 'Southeast' THEN
                (ARRAY['Atlanta','Charlotte','Nashville','Orlando','Miami','Raleigh'])[(s.store_id % 6) + 1]
            WHEN 'Midwest' THEN
                (ARRAY['Chicago','Columbus','Detroit','Cleveland','Indianapolis','Milwaukee'])[(s.store_id % 6) + 1]
            WHEN 'Southwest' THEN
                (ARRAY['Dallas','Austin','Phoenix','Houston','San Antonio','Albuquerque'])[(s.store_id % 6) + 1]
            ELSE
                (ARRAY['Los Angeles','San Diego','Seattle','Portland','San Francisco','Las Vegas'])[(s.store_id % 6) + 1]
        END AS mapped_city,
        CASE s.region
            WHEN 'Northeast' THEN
                (ARRAY['MA','NY','PA','RI','CT','NJ'])[(s.store_id % 6) + 1]
            WHEN 'Southeast' THEN
                (ARRAY['GA','NC','TN','FL','FL','NC'])[(s.store_id % 6) + 1]
            WHEN 'Midwest' THEN
                (ARRAY['IL','OH','MI','OH','IN','WI'])[(s.store_id % 6) + 1]
            WHEN 'Southwest' THEN
                (ARRAY['TX','TX','AZ','TX','TX','NM'])[(s.store_id % 6) + 1]
            ELSE
                (ARRAY['CA','CA','WA','OR','CA','NV'])[(s.store_id % 6) + 1]
        END AS mapped_state,
        CASE s.region
            WHEN 'Northeast' THEN
                (ARRAY['Boylston Street','Fifth Avenue','Market Street','Main Street','Broad Street','Canal Street'])[(s.store_id % 6) + 1]
            WHEN 'Southeast' THEN
                (ARRAY['Peachtree Street','Tryon Street','Broadway','Orange Avenue','Biscayne Boulevard','Hillsborough Street'])[(s.store_id % 6) + 1]
            WHEN 'Midwest' THEN
                (ARRAY['Michigan Avenue','High Street','Woodward Avenue','Euclid Avenue','Meridian Street','Wisconsin Avenue'])[(s.store_id % 6) + 1]
            WHEN 'Southwest' THEN
                (ARRAY['Elm Street','Congress Avenue','Camelback Road','Westheimer Road','Commerce Street','Central Avenue'])[(s.store_id % 6) + 1]
            ELSE
                (ARRAY['Sunset Boulevard','Gaslamp Quarter','Pine Street','NW 23rd Avenue','Market Street','Las Vegas Boulevard'])[(s.store_id % 6) + 1]
        END AS mapped_street
    FROM retail_core.stores s
),
normalized AS (
    SELECT
        store_id,
        CASE WHEN store_id = 56 THEN 'Northeast' ELSE region END AS region,
        CASE WHEN store_id = 56 THEN 'Boston' ELSE mapped_city END AS city,
        CASE WHEN store_id = 56 THEN 'MA' ELSE mapped_state END AS state_code,
        CASE WHEN store_id = 56 THEN 'Boylston Street' ELSE mapped_street END AS street_address
    FROM region_city_map
),
formatted AS (
    SELECT
        store_id,
        region,
        city,
        state_code,
        street_address,
        CONCAT(100 + store_id, ' ', street_address) AS full_street,
        LPAD((10000 + (store_id * 37) % 89999)::TEXT, 5, '0') AS postal_code,
        CONCAT(city, ' - ', street_address, ' Location') AS store_name
    FROM normalized
)
UPDATE retail_core.stores s
SET
    region = f.region,
    city = f.city,
    state_code = f.state_code,
    street_address = f.full_street,
    postal_code = f.postal_code,
    store_name = f.store_name
FROM formatted f
WHERE s.store_id = f.store_id;

UPDATE retail_usecases.inventory i
SET
    store_name = s.store_name,
    region = s.region
FROM retail_core.stores s
WHERE i.store_id = s.store_id;
