#!/usr/bin/env python3
"""Deeper check - use English to avoid encoding issues"""
import sqlite3
conn = sqlite3.connect("icd_kb.db")
cur = conn.cursor()

# Get schema for icd9_clinical_map
cur.execute("PRAGMA table_info(icd9_clinical_map)")
print("=== icd9_clinical_map columns ===")
for r in cur.fetchall():
    print(f"  {r}")

# Get all table names again
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"\n=== All tables ({len(tables)}) ===")
for t in tables:
    print(f"  {t}")

# Check adrg_procedure_map schema more carefully
cur.execute("PRAGMA table_info(adrg_procedure_map)")
print("\n=== adrg_procedure_map columns ===")
for r in cur.fetchall():
    print(f"  {r}")

# Check adrg_diagnosis_map schema
cur.execute("PRAGMA table_info(adrg_diagnosis_map)")
print("\n=== adrg_diagnosis_map columns ===")
for r in cur.fetchall():
    print(f"  {r}")

# Count total codes in adrg_procedure_map
cur.execute("SELECT COUNT(DISTINCT icd9_code) FROM adrg_procedure_map")
print(f"\n=== Distinct icd9_codes in adrg_procedure_map: {cur.fetchone()[0]} ===")

# Check if any code starting with 93 exists
cur.execute("SELECT COUNT(*) FROM adrg_procedure_map WHERE icd9_code LIKE '93.%'")
cnt93 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM adrg_procedure_map WHERE icd9_code LIKE '093.%'")
cnt093 = cur.fetchone()[0]
print(f"  93.* count: {cnt93}")
print(f"  093.* count: {cnt093}")

if cnt93 > 0:
    cur.execute("SELECT icd9_code FROM adrg_procedure_map WHERE icd9_code LIKE '93.%' LIMIT 20")
    print("  93.* samples:")
    for r in cur.fetchall():
        print(f"    {r[0]}")
else:
    # Maybe codes in adrg_procedure_map are just 3-4 digit numbers?
    cur.execute("SELECT icd9_code FROM adrg_procedure_map LIMIT 10")
    print("  Sample codes from adrg_procedure_map:")
    for r in cur.fetchall():
        print(f"    [{r[0]}]")

# Check chapter codes table
cur.execute("PRAGMA table_info(icd9_chapters)")
print("\n=== icd9_chapters columns ===")
try:
    for r in cur.fetchall():
        print(f"  {r}")
except:
    print("  table not found")

# Check if there's a separate DRG mapping that links via 医保编码
print("\n=== Searching for tables that might link 医保编码 to DRG ===")
for t in tables:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in cur.fetchall()]
    col_str = "|".join(cols)
    if "医保" in col_str or "clinical" in t.lower() or "map" in t.lower():
        print(f"  {t}: {col_str}")

conn.close()
