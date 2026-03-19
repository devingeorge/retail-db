ALTER TABLE retail_core.customers
ADD COLUMN IF NOT EXISTS email TEXT;

UPDATE retail_core.customers
SET email = CONCAT('customer', customer_id, '@example.com')
WHERE email IS NULL;

ALTER TABLE retail_core.customers
ALTER COLUMN email SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'customers_email_key'
          AND conrelid = 'retail_core.customers'::regclass
    ) THEN
        ALTER TABLE retail_core.customers
        ADD CONSTRAINT customers_email_key UNIQUE (email);
    END IF;
END $$;
