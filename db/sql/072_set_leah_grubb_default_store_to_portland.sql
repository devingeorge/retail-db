UPDATE retail_core.customers
SET preferred_store_id = 121
WHERE LOWER(first_name) = 'leah'
  AND LOWER(last_name) = 'grubb';
