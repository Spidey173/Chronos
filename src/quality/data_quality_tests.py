"""
Chronos - Data Quality & Integrity Test Suite
Automated validation checks ensuring temporal consistency and data reliability.

Tests:
1. SCD2 Single-Active Check: No entity should have >1 active record per address_type.
2. Temporal Window Validity: valid_from must be strictly less than valid_to on retired records.
3. Referential Integrity: Fact transactions must not contain orphan customers or accounts.
4. Non-Null Constraints: Critical metrics (amount, timestamp) must have zero NULLs.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "silver", "banking_warehouse.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def test_single_active_scd2(cursor):
    """TEST 1: Verify each customer has at most ONE active record per address_type."""
    query = """
    SELECT customer_id, address_type, COUNT(*) as active_count
    FROM dim_customer_addresses
    WHERE is_current = 1
    GROUP BY customer_id, address_type
    HAVING COUNT(*) > 1;
    """
    cursor.execute(query)
    violations = cursor.fetchall()
    passed = len(violations) == 0
    return {
        "name": "SCD Type 2 Single-Active Uniqueness",
        "passed": passed,
        "details": f"{len(violations)} violating entities found." if not passed else "All entities have at most 1 active record."
    }

def test_temporal_window_validity(cursor):
    """TEST 2: Verify valid_from < valid_to for all closed records."""
    query = """
    SELECT customer_address_id, valid_from, valid_to
    FROM dim_customer_addresses
    WHERE is_current = 0 AND valid_from >= valid_to;
    """
    cursor.execute(query)
    violations = cursor.fetchall()
    passed = len(violations) == 0
    return {
        "name": "Temporal Validity (valid_from < valid_to)",
        "passed": passed,
        "details": f"{len(violations)} inverted time ranges found." if not passed else "All retired records have valid chronological windows."
    }

def test_referential_integrity(cursor):
    """TEST 3: Verify fact_transactions has zero orphan foreign keys."""
    query = """
    SELECT COUNT(*) 
    FROM fact_transactions t
    LEFT JOIN dim_customers c ON t.customer_id = c.customer_id
    LEFT JOIN dim_accounts a ON t.account_id = a.account_id
    WHERE c.customer_id IS NULL OR a.account_id IS NULL;
    """
    cursor.execute(query)
    orphan_count = cursor.fetchone()[0]
    passed = orphan_count == 0
    return {
        "name": "Fact-to-Dimension Referential Integrity",
        "passed": passed,
        "details": f"{orphan_count} orphan transactions detected." if not passed else "Zero orphan transactions. 100% referential integrity."
    }

def test_fact_completeness(cursor):
    """TEST 4: Check for missing or corrupted transaction values."""
    query = """
    SELECT COUNT(*) 
    FROM fact_transactions
    WHERE amount IS NULL OR amount <= 0 OR txn_timestamp IS NULL;
    """
    cursor.execute(query)
    bad_count = cursor.fetchone()[0]
    passed = bad_count == 0
    return {
        "name": "Transaction Fact Completeness",
        "passed": passed,
        "details": f"{bad_count} records with invalid/null values." if not passed else "All transaction values positive and non-null."
    }

def run_all_tests():
    print(f"\n=======================================================")
    print(f"  Executing Data Quality & Integrity Test Suite")
    print(f"=======================================================")

    conn = get_connection()
    cursor = conn.cursor()

    tests = [
        test_single_active_scd2(cursor),
        test_temporal_window_validity(cursor),
        test_referential_integrity(cursor),
        test_fact_completeness(cursor)
    ]

    conn.close()

    all_passed = True
    print("\nTest Results Summary:")
    print("-" * 75)
    for t in tests:
        status = "[PASS] ✅" if t["passed"] else "[FAIL] ❌"
        if not t["passed"]:
            all_passed = False
        print(f"  {status} {t['name']:<42} | {t['details']}")
    print("-" * 75)

    if all_passed:
        print("\n  [SUCCESS] All 4 data quality tests passed with 100% score!\n")
    else:
        print("\n  [WARNING] Some data quality tests failed. Investigate above logs.\n")
    return all_passed

if __name__ == "__main__":
    run_all_tests()
