"""
Chronos - Silver Layer Transformation & SCD Type 2 Engine
Processes staged raw data into cleansed Silver dimension & fact tables.

Key Operations:
1. SCD Type 1 Upserts: dim_customers, dim_accounts
2. Address Master Normalization: dim_addresses
3. SCD Type 2 Temporal Processing: dim_customer_addresses
   - Detects address changes per (customer_id, address_type)
   - Retires existing active row: is_current=0, valid_to=new_effective_date
   - Inserts new active row: is_current=1, valid_from=new_effective_date, valid_to=NULL
4. Fact Ingestion: fact_transactions (append-only ledger)
"""

import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "silver", "banking_warehouse.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def process_customers(cursor, batch_name):
    """Processes customer records using SCD Type 1 (in-place update)."""
    sql = """
    INSERT INTO dim_customers (
        customer_id, first_name, last_name, email, phone, date_of_birth, kyc_status
    )
    SELECT customer_id, first_name, last_name, email, phone, date_of_birth, kyc_status
    FROM stg_raw_customers
    WHERE _source_batch = ?
    ON CONFLICT(customer_id) DO UPDATE SET
        email = excluded.email,
        phone = excluded.phone,
        kyc_status = excluded.kyc_status;
    """
    cursor.execute(sql, (batch_name,))
    print(f"  [*] dim_customers: Processed customer records.")

def process_addresses_master(cursor, batch_name):
    """Inserts unique physical addresses into the master address dimension."""
    sql = """
    INSERT OR IGNORE INTO dim_addresses (
        address_id, address_line_1, city, state, pincode, country
    )
    SELECT DISTINCT address_id, address_line_1, city, state, pincode, country
    FROM stg_raw_addresses
    WHERE _source_batch = ?;
    """
    cursor.execute(sql, (batch_name,))
    print(f"  [*] dim_addresses: Updated master address catalog.")

def process_scd2_addresses(cursor, batch_name):
    """
    Executes the SCD Type 2 logic for dim_customer_addresses.
    Detects if an active address for a customer and address_type has changed.
    """
    # Fetch incoming addresses for this batch
    cursor.execute("""
        SELECT customer_id, address_id, address_type, effective_date
        FROM stg_raw_addresses
        WHERE _source_batch = ?;
    """, (batch_name,))
    incoming_addresses = cursor.fetchall()

    expired_count = 0
    new_version_count = 0

    for cust_id, addr_id, addr_type, eff_date in incoming_addresses:
        # Check current active record in dim_customer_addresses
        cursor.execute("""
            SELECT customer_address_id, address_id, valid_from
            FROM dim_customer_addresses
            WHERE customer_id = ? AND address_type = ? AND is_current = 1;
        """, (cust_id, addr_type))
        current_active = cursor.fetchone()

        if current_active is None:
            # Case 1: First time this customer/type is registered -> Insert fresh active record
            cursor.execute("""
                INSERT INTO dim_customer_addresses (
                    customer_id, address_id, address_type, valid_from, valid_to, is_current
                ) VALUES (?, ?, ?, ?, NULL, 1);
            """, (cust_id, addr_id, addr_type, eff_date))
            new_version_count += 1
        elif current_active[1] != addr_id:
            # Case 2: Address has CHANGED!
            # A. Expire previous version
            prev_surrogate_key = current_active[0]
            cursor.execute("""
                UPDATE dim_customer_addresses
                SET is_current = 0, valid_to = ?
                WHERE customer_address_id = ?;
            """, (eff_date, prev_surrogate_key))
            expired_count += 1

            # B. Insert new active version
            cursor.execute("""
                INSERT INTO dim_customer_addresses (
                    customer_id, address_id, address_type, valid_from, valid_to, is_current
                ) VALUES (?, ?, ?, ?, NULL, 1);
            """, (cust_id, addr_id, addr_type, eff_date))
            new_version_count += 1
            print(f"      -> [SCD2 EVENT] Customer {cust_id} ({addr_type}) changed address: {current_active[1]} -> {addr_id}")
        else:
            # Case 3: Same address already active -> No-op (idempotent)
            pass

    print(f"  [*] dim_customer_addresses (SCD2): {new_version_count} inserted, {expired_count} expired.")

def process_accounts(cursor, batch_name):
    """Processes bank accounts."""
    sql = """
    INSERT INTO dim_accounts (
        account_id, customer_id, account_type, account_status, opened_date, branch_code
    )
    SELECT account_id, customer_id, account_type, account_status, opened_date, branch_code
    FROM stg_raw_accounts
    WHERE _source_batch = ?
    ON CONFLICT(account_id) DO UPDATE SET
        account_status = excluded.account_status;
    """
    cursor.execute(sql, (batch_name,))
    print(f"  [*] dim_accounts: Processed accounts.")

def process_transactions(cursor, batch_name):
    """Appends transactions into fact_transactions."""
    sql = """
    INSERT OR IGNORE INTO fact_transactions (
        transaction_id, account_id, customer_id, txn_type, amount, currency, merchant_city, channel, txn_timestamp
    )
    SELECT transaction_id, account_id, customer_id, txn_type, CAST(amount AS DECIMAL(14,2)), currency, merchant_city, channel, txn_timestamp
    FROM stg_raw_transactions
    WHERE _source_batch = ?;
    """
    cursor.execute(sql, (batch_name,))
    print(f"  [*] fact_transactions: Appended transactions.")

def run_pipeline(batch_name):
    print(f"\n=======================================================")
    print(f"  Executing Silver Transformation Engine: {batch_name}")
    print(f"=======================================================")

    conn = get_connection()
    cursor = conn.cursor()

    process_customers(cursor, batch_name)
    process_addresses_master(cursor, batch_name)
    process_scd2_addresses(cursor, batch_name)
    process_accounts(cursor, batch_name)
    process_transactions(cursor, batch_name)

    conn.commit()
    conn.close()
    print(f"  [SUCCESS] Silver layer updated for {batch_name}.\n")

if __name__ == "__main__":
    batch = sys.argv[1] if len(sys.argv) > 1 else "batch_2024_01_01"
    run_pipeline(batch)
