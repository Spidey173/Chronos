-- ==============================================================================
-- CHRONOS: SCD TYPE 2 TRANSFORMATION PATTERNS (SILVER LAYER)
-- How to handle Slowly Changing Dimensions in SQL
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. SCD TYPE 1 UPDATE: CUSTOMERS (In-Place Overwrite)
-- When a customer's phone or KYC status updates, we update in-place.
-- ------------------------------------------------------------------------------
INSERT INTO dim_customers (
    customer_id, first_name, last_name, email, phone, date_of_birth, kyc_status
)
SELECT 
    customer_id, first_name, last_name, email, phone, date_of_birth, kyc_status
FROM stg_raw_customers
WHERE _source_batch = :batch_name
ON CONFLICT(customer_id) DO UPDATE SET
    email = excluded.email,
    phone = excluded.phone,
    kyc_status = excluded.kyc_status;


-- ------------------------------------------------------------------------------
-- 2. MASTER ADDRESS CATALOG INSERTION (Deduplicated)
-- ------------------------------------------------------------------------------
INSERT OR IGNORE INTO dim_addresses (
    address_id, address_line_1, city, state, pincode, country
)
SELECT DISTINCT 
    address_id, address_line_1, city, state, pincode, country
FROM stg_raw_addresses
WHERE _source_batch = :batch_name;


-- ------------------------------------------------------------------------------
-- 3. SCD TYPE 2 PATTERN: EXPIRE OLD ADDRESS (Step A: Retirement)
-- If the customer already has an active address for this type, but the new batch
-- has a different address_id, mark the old record as expired.
-- ------------------------------------------------------------------------------
UPDATE dim_customer_addresses
SET 
    is_current = 0,
    valid_to = (
        SELECT stg.effective_date
        FROM stg_raw_addresses stg
        WHERE stg.customer_id = dim_customer_addresses.customer_id
          AND stg.address_type = dim_customer_addresses.address_type
          AND stg._source_batch = :batch_name
    )
WHERE is_current = 1
  AND EXISTS (
      SELECT 1 
      FROM stg_raw_addresses stg
      WHERE stg.customer_id = dim_customer_addresses.customer_id
        AND stg.address_type = dim_customer_addresses.address_type
        AND stg.address_id <> dim_customer_addresses.address_id
        AND stg._source_batch = :batch_name
  );


-- ------------------------------------------------------------------------------
-- 4. SCD TYPE 2 PATTERN: INSERT NEW VERSION (Step B: Insertion)
-- Insert the new address with valid_from = effective_date, valid_to = NULL, is_current = 1
-- ------------------------------------------------------------------------------
INSERT INTO dim_customer_addresses (
    customer_id, address_id, address_type, valid_from, valid_to, is_current
)
SELECT 
    stg.customer_id,
    stg.address_id,
    stg.address_type,
    stg.effective_date AS valid_from,
    NULL               AS valid_to,
    1                  AS is_current
FROM stg_raw_addresses stg
WHERE stg._source_batch = :batch_name
  -- Only insert if there isn't ALREADY an identical active record
  AND NOT EXISTS (
      SELECT 1 
      FROM dim_customer_addresses curr
      WHERE curr.customer_id = stg.customer_id
        AND curr.address_id = stg.address_id
        AND curr.address_type = stg.address_type
        AND curr.is_current = 1
  );
