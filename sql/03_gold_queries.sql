-- ==============================================================================
-- CHRONOS: GOLD LAYER ANALYTICS & AUDIT MARTS
-- Serving views for Regulatory Compliance, Fraud Detection, and Customer 360
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. POINT-IN-TIME TRANSACTION AUDIT VIEW
-- Every financial transaction enriched with the customer's exact physical address
-- at the millisecond the transaction was executed.
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS view_point_in_time_transactions AS
SELECT 
    t.transaction_id,
    t.txn_timestamp,
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    t.account_id,
    t.txn_type,
    t.amount,
    t.merchant_city AS transaction_location,
    t.channel,
    a.city          AS registered_city_at_txn_time,
    a.state         AS registered_state_at_txn_time,
    a.pincode       AS registered_pincode_at_txn_time,
    ca.address_type,
    ca.valid_from   AS address_effective_from,
    ca.valid_to     AS address_effective_to
FROM fact_transactions t
JOIN dim_customers c 
    ON t.customer_id = c.customer_id
JOIN dim_customer_addresses ca 
    ON t.customer_id = ca.customer_id
   AND ca.address_type = 'COMMUNICATION'
   -- The Core Point-in-Time Temporal Range Join:
   AND t.txn_timestamp >= ca.valid_from
   AND (t.txn_timestamp < ca.valid_to OR ca.valid_to IS NULL)
JOIN dim_addresses a 
    ON ca.address_id = a.address_id;


-- ------------------------------------------------------------------------------
-- 2. GEOGRAPHIC ANOMALY & FRAUD ALERT VIEW
-- Identifies transactions where physical channel (ATM / POS) took place in a city
-- completely different from the customer's active communication address at that time.
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS view_fraud_geo_mismatch_alerts AS
SELECT 
    pit.transaction_id,
    pit.txn_timestamp,
    pit.customer_id,
    pit.customer_name,
    pit.amount,
    pit.channel,
    pit.transaction_location,
    pit.registered_city_at_txn_time,
    CASE 
        WHEN pit.transaction_location <> pit.registered_city_at_txn_time 
             AND pit.channel IN ('ATM', 'POS_PURCHASE') 
        THEN 'HIGH_RISK_GEO_MISMATCH'
        ELSE 'NORMAL'
    END AS risk_classification
FROM view_point_in_time_transactions pit;


-- ------------------------------------------------------------------------------
-- 3. CUSTOMER 360 COMPREHENSIVE FINANCIAL MART
-- Single pane of glass for account balances, KYC standing, active location, and activity.
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS view_customer_360_mart AS
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS full_name,
    c.email,
    c.phone,
    c.kyc_status,
    curr_addr.city AS current_city,
    curr_addr.state AS current_state,
    COUNT(DISTINCT a.account_id) AS total_accounts,
    COUNT(DISTINCT t.transaction_id) AS total_transactions,
    COALESCE(SUM(CASE WHEN t.txn_type = 'DEPOSIT' THEN t.amount ELSE 0 END), 0) AS total_deposited,
    COALESCE(SUM(CASE WHEN t.txn_type IN ('WITHDRAWAL', 'POS_PURCHASE') THEN t.amount ELSE 0 END), 0) AS total_spent_or_withdrawn
FROM dim_customers c
LEFT JOIN dim_customer_addresses ca 
    ON c.customer_id = ca.customer_id 
   AND ca.address_type = 'COMMUNICATION' 
   AND ca.is_current = 1
LEFT JOIN dim_addresses curr_addr 
    ON ca.address_id = curr_addr.address_id
LEFT JOIN dim_accounts a 
    ON c.customer_id = a.customer_id
LEFT JOIN fact_transactions t 
    ON c.customer_id = t.customer_id
GROUP BY 
    c.customer_id, full_name, c.email, c.phone, c.kyc_status, current_city, current_state;
