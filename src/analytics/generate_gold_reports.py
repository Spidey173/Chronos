"""
Chronos - Gold Layer Report Exporter
Queries the Gold analytical views and exports CSV/JSON business marts into data/gold/.

Exports:
1. point_in_time_audit_report.csv
2. fraud_geo_mismatch_alerts.csv
3. customer_360_executive_mart.csv
"""

import os
import csv
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "silver", "banking_warehouse.db")
GOLD_DIR = os.path.join(BASE_DIR, "data", "gold")

def get_connection():
    return sqlite3.connect(DB_PATH)

def export_view_to_csv(cursor, view_name, output_filename):
    os.makedirs(GOLD_DIR, exist_ok=True)
    out_path = os.path.join(GOLD_DIR, output_filename)
    
    cursor.execute(f"SELECT * FROM {view_name};")
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]

    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerows(rows)

    print(f"  [+] Exported {view_name} -> data/gold/{output_filename} ({len(rows)} records)")

def run_gold_exports():
    print(f"\n=======================================================")
    print(f"  Generating Gold Layer Business Marts & Audit Reports")
    print(f"=======================================================")

    conn = get_connection()
    cursor = conn.cursor()

    export_view_to_csv(cursor, "view_point_in_time_transactions", "point_in_time_audit_report.csv")
    export_view_to_csv(cursor, "view_fraud_geo_mismatch_alerts", "fraud_geo_mismatch_alerts.csv")
    export_view_to_csv(cursor, "view_customer_360_mart", "customer_360_executive_mart.csv")

    conn.close()
    print(f"  [SUCCESS] All Gold analytical marts generated successfully.\n")

if __name__ == "__main__":
    run_gold_exports()
