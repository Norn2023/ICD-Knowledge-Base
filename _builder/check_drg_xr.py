#!/usr/bin/env python3
"""Check all relevant data about 联合物理治疗 and DRG grouping"""
import sqlite3, re
conn = sqlite3.connect("icd_kb.db")
cur = conn.cursor()

# 1. Check if 93.38 is in no_group_px (不作为主手术)
print("=== no_group_px: 93.38* ===")
cur.execute("SELECT * FROM no_group_px WHERE icd9_code LIKE '%93.38%'")
for r in cur.fetchall():
    print(f"  {r}")

# 2. Check all ADRGs that relate to rehabilitation
print("\n=== drg_adrg: 康复相关 ===")
cur.execute("SELECT adrg_code, name FROM drg_adrg WHERE name LIKE '%康复%'")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]}")

# 3. Check drg_groups under those ADRGs
print("\n=== drg_groups: XR ADRGs ===")
cur.execute("""
    SELECT a.adrg_code, a.name, g.drg_code, g.name, g.severity
    FROM drg_groups g
    JOIN drg_adrg a ON a.id = g.adrg_id
    WHERE a.adrg_code LIKE 'XR%'
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} → {r[2]} | {r[3]} ({r[4]})")

# 4. Check all diagnosis codes mapped to XR ADRGs
print("\n=== adrg_diagnosis_map: XR ADRGs ===")
cur.execute("""
    SELECT a.adrg_code, a.name, d.icd10_code
    FROM adrg_diagnosis_map d
    JOIN drg_adrg a ON a.id = d.adrg_id
    WHERE a.adrg_code LIKE 'XR%'
    ORDER BY d.icd10_code
""")
rows = cur.fetchall()
print(f"  共 {len(rows)} 条")
for r in rows[:30]:
    print(f"  {r[0]} | {r[1]} ← {r[2]}")
if len(rows) > 30:
    print(f"  ... (还有 {len(rows)-30} 条)")

# 5. Check Z50 codes in icd10_codes
print("\n=== icd10_codes: Z50* ===")
cur.execute("SELECT code, name FROM icd10_codes WHERE code LIKE 'Z50%'")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]}")

# 6. Check the actual page code to see what f9() searches
print("\n=== Checking how DRG page filters procedures ===")

# 7. Check if adrg_procedure_map has any XR ADRG entries
print("\n=== adrg_procedure_map: XR ADRGs ===")
cur.execute("""
    SELECT p.icd9_code, a.adrg_code, a.name
    FROM adrg_procedure_map p
    JOIN drg_adrg a ON a.id = p.adrg_id
    WHERE a.adrg_code LIKE 'XR%'
""")
for r in cur.fetchall():
    print(f"  {r[1]} | {r[2]} ← {r[0]}")

# 8. Check the ADRG that Z50.100x001 maps to
print("\n=== Z50.100x001 diagnosis-to-ADRG mapping ===")
cur.execute("""
    SELECT a.adrg_code, a.name, d.icd10_code
    FROM adrg_diagnosis_map d
    JOIN drg_adrg a ON a.id = d.adrg_id
    WHERE d.icd10_code = 'Z50.100x001'
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} ← {r[2]}")

conn.close()
