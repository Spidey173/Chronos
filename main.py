"""
Chronos - End-to-End Pipeline Master Orchestrator
Executes the full data lifecycle from Bronze ingestion to Gold analytical marts.

Usage:
    python3 main.py
"""

import os
import sys
import sqlite3
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "silver", "banking_warehouse.db")

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)

def step_0_init_database(clean_start=True):
    print_header("Step 0: Initializing Silver Warehouse DDL")
    if clean_start and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  [+] Reset existing database: {DB_PATH}")

    ddl_path = os.path.join(BASE_DIR, "sql", "01_ddl_schema.sql")
    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl_sql = f.read()

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(ddl_sql)
    conn.commit()
    conn.close()
    print("  [+] Fresh database schema initialized successfully.")

def step_1_generate_mock_data():
    print_header("Step 1: Generating Mock Core Banking Feeds")
    from src.generator.generate_mock_data import generate_batch_1, generate_batch_2
    generate_batch_1()
    generate_batch_2()

def step_2_ingest_and_transform_batch(batch_name):
    print_header(f"Processing Batch: {batch_name}")
    from src.ingestion.ingest_bronze import ingest_batch
    from src.transforms.scd2_engine import run_pipeline

    print(f"  --> Ingesting raw files into Bronze staging...")
    ingest_batch(batch_name)

    print(f"  --> Executing Silver Transformation & SCD Type 2 Engine...")
    run_pipeline(batch_name)

def step_3_apply_gold_views():
    print_header("Step 3: Creating Gold Layer Analytical Views")
    gold_sql_path = os.path.join(BASE_DIR, "sql", "03_gold_queries.sql")
    with open(gold_sql_path, "r", encoding="utf-8") as f:
        gold_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(gold_sql)
    conn.commit()
    conn.close()
    print("  [+] Gold views registered in data warehouse.")

def step_4_export_gold_reports():
    print_header("Step 4: Exporting Business Marts & Audit Reports")
    from src.analytics.generate_gold_reports import run_gold_exports
    run_gold_exports()

def step_5_run_quality_checks():
    print_header("Step 5: Executing Automated Data Quality Tests")
    from src.quality.data_quality_tests import run_all_tests
    return run_all_tests()

def main():
    print("\n" + "#" * 70)
    print("   CHRONOS - END-TO-END DATA PIPELINE EXECUTION")
    print("#" * 70)

    # 1. Reset / Initialize DDL
    step_0_init_database()

    # 2. Generate simulated banking feeds
    step_1_generate_mock_data()

    # 3. Process Batch 1 (2024-01-01 Baseline)
    step_2_ingest_and_transform_batch("batch_2024_01_01")

    # 4. Process Batch 2 (2026-05-11 Relocation & State Change)
    step_2_ingest_and_transform_batch("batch_2026_05_11")

    # 5. Build Gold Layer Views
    step_3_apply_gold_views()

    # 6. Export Reports
    step_4_export_gold_reports()

    # 7. Run Data Quality Suite
    tests_passed = step_5_run_quality_checks()

    print("\n" + "#" * 70)
    if tests_passed:
        print("   PIPELINE RUN COMPLETED SUCCESSFULLY: ALL STAGES & TESTS PASSED!")
    else:
        print("   PIPELINE FINISHED WITH QUALITY WARNINGS!")
    print("#" * 70 + "\n")

if __name__ == "__main__":
    main()
