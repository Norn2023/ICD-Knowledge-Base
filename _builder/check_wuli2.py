#!/usr/bin/env python3
"""Deeper check on 联合物理治疗 and its DRG relations"""
import sqlite3
conn = sqlite3.connect("icd_kb.db")
cur = conn.cursor()

# 1. Check what format codes in adrg_procedure_map look like (sample)
print("=== adrg_procedure_map 编码格式样本 ===")
cur.execute("SELECT icd9_code FROM adrg_procedure_map LIMIT 20")
for r in cur.fetchall():
    print(f"  [{r[0]}]")

# 2. Check if 970301000 (医保编码) is in adrg_procedure_map
print("\n=== 医保编码 970301000 在 adrg_procedure_map 中? ===")
cur.execute("SELECT * FROM adrg_procedure_map WHERE icd9_code = '970301000'")
r = cur.fetchone()
if r:
    print(f"  找到: adrg_id={r[0]}")
else:
    print("  未找到")

# 3. Check icd9_clinical_map for 联合物理治疗
print("\n=== icd9_clinical_map: 970301000 ===")
cur.execute("SELECT * FROM icd9_clinical_map WHERE 医保编码 = '970301000'")
cols = [d[0] for d in cur.description]
r = cur.fetchone()
if r:
    for i, c in enumerate(cols):
        print(f"  {c} = {r[i]}")
else:
    print("  未找到")

# 4. Check what tables exist and their schemas
print("\n=== 所有表 ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for r in cur.fetchall():
    cur2 = conn.cursor()
    cur2.execute(f"PRAGMA table_info({r[0]})")
    cols = cur2.fetchall()
    print(f"\n  {r[0]}:")
    for c in cols:
        print(f"    {c[1]} ({c[2]})")

# 5. Check adrg table for rehabilitation related groups
print("\n=== ADRG表中康复相关分组 ===")
cur.execute("SELECT code, name, mdc_id FROM adrg_codes WHERE name LIKE '%康复%' OR name LIKE '%物理%' OR name LIKE '%理疗%'")
for r in cur.fetchall():
    print(f"  code={r[0]}, name={r[1]}, mdc={r[2]}")

# 6. Check all adrg_procedure_map entries linked to 康复 ADRGs
print("\n=== 康复相关ADRG下的手术编码 ===")
cur.execute("""
    SELECT p.icd9_code, p.adrg_id, a.name as adrg_name
    FROM adrg_procedure_map p
    JOIN adrg_codes a ON a.id = p.adrg_id
    WHERE a.name LIKE '%康复%' OR a.name LIKE '%物理%' OR a.name LIKE '%理疗%'
""")
for r in cur.fetchall():
    print(f"  icd9={r[0]}, adrg_id={r[1]}, adrg_name={r[2]}")

# 7. Check if adrg_procedure_map has any 93.* codes at all
print("\n=== adrg_procedure_map: 93.* 编码统计 ===")
cur.execute("SELECT COUNT(*) FROM adrg_procedure_map WHERE icd9_code LIKE '93.%'")
print(f"  93.* 编码数量: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM adrg_procedure_map WHERE icd9_code LIKE '093.%'")
print(f"  093.* 编码数量: {cur.fetchone()[0]}")

# 8. Sample of 93.* codes in adrg_procedure_map
print("\n=== adrg_procedure_map: 93.* 编码样本 ===")
cur.execute("SELECT icd9_code FROM adrg_procedure_map WHERE icd9_code LIKE '93.%' LIMIT 30")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Same for 093.*
print("\n=== adrg_procedure_map: 093.* 编码样本 ===")
cur.execute("SELECT icd9_code FROM adrg_procedure_map WHERE icd9_code LIKE '093.%' LIMIT 30")
for r in cur.fetchall():
    print(f"  {r[0]}")

conn.close()
