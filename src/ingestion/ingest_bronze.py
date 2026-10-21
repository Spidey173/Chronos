"""
Chronos - Bronze Ingestion Engine
Loads raw source extracts into staging tables with lineage metadata.

Key Principles:
1. Append-only, zero business transformation (preserves raw truth).
2. Attaches ELT audit metadata (_source_batch, _ingested_at) for lineage and debugging.
"""

import os
import sys
import csv
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "silver", "banking_warehouse.db")
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_staging_tables(cursor):
    """Creates staging tables with audit columns if they don't already exist."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stg_raw_customers (
        customer_id     TEXT,
        first_name      TEXT,
        last_name       TEXT,
        email           TEXT,
        phone           TEXT,
        date_of_birth   TEXT,
        kyc_status      TEXT,
        feed_timestamp  TEXT,
        _source_batch   TEXT,
        _ingested_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stg_raw_addresses (
        address_id      TEXT,
        customer_id     TEXT,
        address_type    TEXT,
        address_line_1  TEXT,
        city            TEXT,
        state           TEXT,
        pincode         TEXT,
        country         TEXT,
        effective_date  TEXT,
        _source_batch   TEXT,
        _ingested_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stg_raw_accounts (
        account_id      TEXT,
        customer_id     TEXT,
        account_type    TEXT,
        account_status  TEXT,
        opened_date     TEXT,
        branch_code     TEXT,
        _source_batch   TEXT,
        _ingested_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stg_raw_transactions (
        transaction_id  TEXT,
        account_id      TEXT,
        customer_id     TEXT,
        txn_type        TEXT,
        amount          TEXT,
        currency        TEXT,
        merchant_city   TEXT,
        channel         TEXT,
        txn_timestamp   TEXT,
        _source_batch   TEXT,
        _ingested_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

def ingest_file(cursor, filepath, table_name, batch_name):
    """Ingests a CSV file into the designated staging table with lineage metadata."""
    if not os.path.exists(filepath):
        return 0

    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return 0

    fields = list(rows[0].keys())
    fields_with_meta = fields + ["_source_batch", "_ingested_at"]
    placeholders = ", ".join(["?"] * len(fields_with_meta))
    columns_str = ", ".join(fields_with_meta)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_to_insert = [
        [row[col] for col in fields] + [batch_name, now_str]
        for row in rows
    ]

    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    cursor.executemany(sql, data_to_insert)
    return len(rows)

def ingest_batch(batch_name):
    batch_path = os.path.join(BRONZE_DIR, batch_name)
    if not os.path.exists(batch_path):
        print(f"[ERROR] Batch directory not found: {batch_path}")
        return

    print(f"\n=======================================================")
    print(f"  Ingesting Bronze Batch: {batch_name}")
    print(f"=======================================================")

    conn = get_db_connection()
    cursor = conn.cursor()

    init_staging_tables(cursor)

    file_mappings = [
        ("raw_customers.csv", "stg_raw_customers"),
        ("raw_addresses.csv", "stg_raw_addresses"),
        ("raw_accounts.csv", "stg_raw_accounts"),
        ("raw_transactions.csv", "stg_raw_transactions"),
    ]

    total_records = 0
    for filename, table_name in file_mappings:
        filepath = os.path.join(batch_path, filename)
        count = ingest_file(cursor, filepath, table_name, batch_name)
        if count > 0:
            print(f"  [+] Loaded {count} rows into {table_name} from {filename}")
            total_records += count

    conn.commit()
    conn.close()
    print(f"  [SUCCESS] Total {total_records} records staged from {batch_name}.\n")

if __name__ == "__main__":
    target_batch = sys.argv[1] if len(sys.argv) > 1 else "batch_2024_01_01"
    ingest_batch(target_batch)
