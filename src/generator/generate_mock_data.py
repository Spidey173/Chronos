"""
Chronos - Core Banking Mock Data Generator
Simulates daily extract feeds landed in the Bronze Layer.

Generates two chronological batches:
- Batch 1 (2024-01-01): Initial customer onboarding, original addresses, accounts, and early transactions.
- Batch 2 (2026-05-11): Real-world state changes (Customer C101 moves from Udupi to Bangalore, 
  KYC updates, and new transactions in both cities).
"""

import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def write_csv(filepath, fieldnames, rows):
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [+] Created: {filepath} ({len(rows)} records)")

def generate_batch_1():
    batch_dir = os.path.join(BRONZE_DIR, "batch_2024_01_01")
    ensure_dir(batch_dir)
    print("\n--- Generating Batch 1: Initial State (2024-01-01) ---")

    # 1. Customers
    customers = [
        {
            "customer_id": "C101",
            "first_name": "Pruthvi",
            "last_name": "Kumar",
            "email": "pruthvi.k@apexbank.in",
            "phone": "+91-9876543210",
            "date_of_birth": "1998-07-14",
            "kyc_status": "VERIFIED",
            "feed_timestamp": "2024-01-01 09:00:00"
        },
        {
            "customer_id": "C102",
            "first_name": "Ananya",
            "last_name": "Rao",
            "email": "ananya.rao@apexbank.in",
            "phone": "+91-9845012345",
            "date_of_birth": "1995-03-22",
            "kyc_status": "PENDING",
            "feed_timestamp": "2024-01-01 09:15:00"
        },
        {
            "customer_id": "C103",
            "first_name": "Rahul",
            "last_name": "Sharma",
            "email": "rahul.sharma@apexbank.in",
            "phone": "+91-9711098765",
            "date_of_birth": "1992-11-05",
            "kyc_status": "VERIFIED",
            "feed_timestamp": "2024-01-01 09:30:00"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_customers.csv"),
        ["customer_id", "first_name", "last_name", "email", "phone", "date_of_birth", "kyc_status", "feed_timestamp"],
        customers
    )

    # 2. Addresses (Notice: C101 lives in Udupi in 2024)
    addresses = [
        {
            "address_id": "A001",
            "customer_id": "C101",
            "address_type": "COMMUNICATION",
            "address_line_1": "12 Car Street, Near Temple",
            "city": "Udupi",
            "state": "Karnataka",
            "pincode": "576101",
            "country": "India",
            "effective_date": "2024-01-01 00:00:00"
        },
        {
            "address_id": "A001",
            "customer_id": "C101",
            "address_type": "PERMANENT",
            "address_line_1": "12 Car Street, Near Temple",
            "city": "Udupi",
            "state": "Karnataka",
            "pincode": "576101",
            "country": "India",
            "effective_date": "2024-01-01 00:00:00"
        },
        {
            "address_id": "A003",
            "customer_id": "C102",
            "address_type": "COMMUNICATION",
            "address_line_1": "404 Marine Drive, Nariman Point",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400021",
            "country": "India",
            "effective_date": "2024-01-01 00:00:00"
        },
        {
            "address_id": "A004",
            "customer_id": "C103",
            "address_type": "COMMUNICATION",
            "address_line_1": "78 Connaught Place",
            "city": "New Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "country": "India",
            "effective_date": "2024-01-01 00:00:00"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_addresses.csv"),
        ["address_id", "customer_id", "address_type", "address_line_1", "city", "state", "pincode", "country", "effective_date"],
        addresses
    )

    # 3. Accounts
    accounts = [
        {
            "account_id": "ACC1001",
            "customer_id": "C101",
            "account_type": "SAVINGS",
            "account_status": "ACTIVE",
            "opened_date": "2024-01-01",
            "branch_code": "UDP-MAIN-01"
        },
        {
            "account_id": "ACC1002",
            "customer_id": "C102",
            "account_type": "CURRENT",
            "account_status": "ACTIVE",
            "opened_date": "2024-01-01",
            "branch_code": "MUM-NAR-01"
        },
        {
            "account_id": "ACC1003",
            "customer_id": "C103",
            "account_type": "SAVINGS",
            "account_status": "ACTIVE",
            "opened_date": "2024-01-01",
            "branch_code": "DEL-CP-01"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_accounts.csv"),
        ["account_id", "customer_id", "account_type", "account_status", "opened_date", "branch_code"],
        accounts
    )

    # 4. Transactions in 2024 (Notice: C101 legitimately transacting in Udupi)
    transactions = [
        {
            "transaction_id": "TXN20240215001",
            "account_id": "ACC1001",
            "customer_id": "C101",
            "txn_type": "DEPOSIT",
            "amount": "50000.00",
            "currency": "INR",
            "merchant_city": "Udupi",
            "channel": "BRANCH",
            "txn_timestamp": "2024-02-15 10:30:00"
        },
        {
            "transaction_id": "TXN20240620002",
            "account_id": "ACC1001",
            "customer_id": "C101",
            "txn_type": "WITHDRAWAL",
            "amount": "10000.00",
            "currency": "INR",
            "merchant_city": "Udupi",
            "channel": "ATM",
            "txn_timestamp": "2024-06-20 18:45:12"
        },
        {
            "transaction_id": "TXN20240810003",
            "account_id": "ACC1002",
            "customer_id": "C102",
            "txn_type": "POS_PURCHASE",
            "amount": "3499.00",
            "currency": "INR",
            "merchant_city": "Mumbai",
            "channel": "CARD",
            "txn_timestamp": "2024-08-10 14:12:00"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_transactions.csv"),
        ["transaction_id", "account_id", "customer_id", "txn_type", "amount", "currency", "merchant_city", "channel", "txn_timestamp"],
        transactions
    )

def generate_batch_2():
    batch_dir = os.path.join(BRONZE_DIR, "batch_2026_05_11")
    ensure_dir(batch_dir)
    print("\n--- Generating Batch 2: Updates & Relocation (2026-05-11) ---")

    # 1. Customer updates (C102 gets KYC verified)
    customer_updates = [
        {
            "customer_id": "C102",
            "first_name": "Ananya",
            "last_name": "Rao",
            "email": "ananya.rao@apexbank.in",
            "phone": "+91-9845012345",
            "date_of_birth": "1995-03-22",
            "kyc_status": "VERIFIED", # Status changed from PENDING to VERIFIED
            "feed_timestamp": "2026-05-11 11:00:00"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_customers.csv"),
        ["customer_id", "first_name", "last_name", "email", "phone", "date_of_birth", "kyc_status", "feed_timestamp"],
        customer_updates
    )

    # 2. Address updates: C101 moves communication address to Bangalore!
    # Permanent address remains in Udupi!
    address_updates = [
        {
            "address_id": "A002",
            "customer_id": "C101",
            "address_type": "COMMUNICATION",
            "address_line_1": "88 4th Cross, Koramangala 5th Block",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560095",
            "country": "India",
            "effective_date": "2026-05-11 00:00:00"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_addresses.csv"),
        ["address_id", "customer_id", "address_type", "address_line_1", "city", "state", "pincode", "country", "effective_date"],
        address_updates
    )

    # 3. Subsequent Transactions:
    # Notice:
    # 1) C101 transacts in Bangalore (matches new communication address)
    # 2) Suspicious anomaly: C101 has an ATM withdrawal in Kolkata while active in Bangalore
    new_transactions = [
        {
            "transaction_id": "TXN20260515001",
            "account_id": "ACC1001",
            "customer_id": "C101",
            "txn_type": "POS_PURCHASE",
            "amount": "2500.00",
            "currency": "INR",
            "merchant_city": "Bangalore",
            "channel": "UPI",
            "txn_timestamp": "2026-05-15 13:20:00"
        },
        {
            "transaction_id": "TXN20260520999",
            "account_id": "ACC1001",
            "customer_id": "C101",
            "txn_type": "WITHDRAWAL",
            "amount": "80000.00",
            "currency": "INR",
            "merchant_city": "Kolkata", # GEO MISMATCH (Fraud Alert Candidate!)
            "channel": "ATM",
            "txn_timestamp": "2026-05-20 22:45:00"
        }
    ]
    write_csv(
        os.path.join(batch_dir, "raw_transactions.csv"),
        ["transaction_id", "account_id", "customer_id", "txn_type", "amount", "currency", "merchant_city", "channel", "txn_timestamp"],
        new_transactions
    )

if __name__ == "__main__":
    generate_batch_1()
    generate_batch_2()
    print("\n[SUCCESS] Mock core banking extract feeds generated in data/bronze/.")
