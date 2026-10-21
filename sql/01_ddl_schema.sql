-- ==============================================================================
-- CHRONOS: DATA WAREHOUSE DDL (SILVER LAYER)
-- Architecture: Medallion Silver Layer (Cleaned Relational & Dimensional Model)
-- Features: Point-in-Time Temporal Tracking with SCD Type 2
-- ==============================================================================

-- 1. CUSTOMER DIMENSION (SCD Type 1 / Static Demographics)
-- Stores core customer identity. Immutable or overwritten if typo corrected.
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id         VARCHAR(32) PRIMARY KEY,     -- Business Key (e.g., 'C101')
    first_name          VARCHAR(64) NOT NULL,
    last_name           VARCHAR(64) NOT NULL,
    email               VARCHAR(128) UNIQUE NOT NULL,
    phone               VARCHAR(20) NOT NULL,
    date_of_birth       DATE NOT NULL,
    kyc_status          VARCHAR(20) DEFAULT 'PENDING', -- 'VERIFIED', 'PENDING', 'REJECTED'
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ADDRESS MASTER DIMENSION (Normalized Locations)
-- De-duplicated catalog of physical locations.
CREATE TABLE IF NOT EXISTS dim_addresses (
    address_id          VARCHAR(32) PRIMARY KEY,     -- Master Address Key (e.g., 'A001')
    address_line_1      VARCHAR(255) NOT NULL,
    city                VARCHAR(64) NOT NULL,
    state               VARCHAR(64) NOT NULL,
    pincode             VARCHAR(10) NOT NULL,
    country             VARCHAR(64) DEFAULT 'India',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. CUSTOMER-ADDRESS RELATIONSHIP (SCD Type 2 Temporal Dimension)
-- The Heart of History Tracking: Binds customers to addresses across time.
CREATE TABLE IF NOT EXISTS dim_customer_addresses (
    customer_address_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Surrogate Key (Unique per version)
    customer_id         VARCHAR(32) NOT NULL,              -- Business Key linking to Customer
    address_id          VARCHAR(32) NOT NULL,              -- Links to Address master
    address_type        VARCHAR(32) NOT NULL,              -- 'COMMUNICATION', 'PERMANENT', 'OFFICE'
    
    -- Temporal Validity Range (Point-in-Time)
    valid_from          TIMESTAMP NOT NULL,                -- When this address became effective
    valid_to            TIMESTAMP,                         -- When it retired (NULL if currently active)
    is_current          BOOLEAN DEFAULT 1,                 -- 1 (True) for active, 0 (False) for historical
    
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (address_id) REFERENCES dim_addresses(address_id)
);

-- Index for high-speed Point-in-Time joins
CREATE INDEX IF NOT EXISTS idx_cust_addr_pit 
ON dim_customer_addresses (customer_id, valid_from, valid_to);

-- 4. ACCOUNT DIMENSION
-- Financial accounts associated with customers.
CREATE TABLE IF NOT EXISTS dim_accounts (
    account_id          VARCHAR(32) PRIMARY KEY,     -- e.g., 'ACC8801'
    customer_id         VARCHAR(32) NOT NULL,
    account_type        VARCHAR(32) NOT NULL,        -- 'SAVINGS', 'CURRENT', 'FIXED_DEPOSIT'
    account_status      VARCHAR(20) DEFAULT 'ACTIVE',-- 'ACTIVE', 'FROZEN', 'CLOSED'
    opened_date         DATE NOT NULL,
    branch_code         VARCHAR(16) NOT NULL,        -- e.g., 'BLR-KOR-01'
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
);

-- 5. TRANSACTION FACT TABLE
-- High-volume append-only immutable financial events.
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id      VARCHAR(64) PRIMARY KEY,     -- e.g., 'TXN20261001001'
    account_id          VARCHAR(32) NOT NULL,
    customer_id         VARCHAR(32) NOT NULL,
    txn_type            VARCHAR(20) NOT NULL,        -- 'DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'POS_PURCHASE'
    amount              DECIMAL(14, 2) NOT NULL,
    currency            VARCHAR(3) DEFAULT 'INR',
    merchant_city       VARCHAR(64),                 -- Location where the transaction occurred (for fraud audit)
    channel             VARCHAR(20) NOT NULL,        -- 'ATM', 'UPI', 'NET_BANKING', 'CARD'
    txn_timestamp       TIMESTAMP NOT NULL,          -- Exact time transaction was authorized
    FOREIGN KEY (account_id) REFERENCES dim_accounts(account_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id)
);

-- Index for transaction filtering by customer and timestamp
CREATE INDEX IF NOT EXISTS idx_txn_cust_time 
ON fact_transactions (customer_id, txn_timestamp);
