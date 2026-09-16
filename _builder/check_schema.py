#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect("icd_kb.db")
cur = conn.cursor()

# Check schema
cur.execute("PRAGMA table_info(icd9_codes)")
print("=== icd9_codes columns ===")
for r in cur.fetchall():
    print(r)

cur.execute("PRAGMA table_info(adrg_procedure_map)")
print("\n=== adrg_procedure_map columns ===")
for r in cur.fetchall():
    print(r)

# Check any wuli related
cur.execute("SELECT code, name FROM icd9_codes WHERE name LIKE '%物理%' OR name LIKE '%理疗%'")
print("\n=== icd9_codes: 物理治疗 ===")
for r in cur.fetchall():
    print(f"  code={r[0]}, name={r[1]}")

# Check all codes in adrg_procedure_map
print("\n=== adrg_procedure_map: all rows count ===")
cur.execute("SELECT COUNT(*) FROM adrg_procedure_map")
print(f"  总数: {cur.fetchone()[0]}")

# Check adrg_procedure_map for 93.38
cur.execute("SELECT icd9_code FROM adrg_procedure_map WHERE icd9_code = '93.3800x001' OR icd9_code = '93.3800' OR icd9_code = '093.3800' OR icd9_code = '093.3800x001'")
print("\n=== adrg_procedure_map: 联合物理治疗精确匹配 ===")
for r in cur.fetchall():
    print(f"  找到: {r[0]}")

# Check 93.38 pattern in adrg_procedure_map
cur.execute("SELECT icd9_code FROM adrg_procedure_map WHERE icd9_code LIKE '%93.38%'")
rows = cur.fetchall()
print(f"\n=== adrg_procedure_map: 包含93.38的编码 (共{len(rows)}条) ===")
for r in rows[:50]:
    print(f"  {r[0]}")
if len(rows) > 50:
    print(f"  ... (还有{len(rows)-50}条)")

# Check 093.38 pattern
cur.execute("SELECT icd9_code FROM adrg_procedure_map WHERE icd9_code LIKE '%093.38%'")
rows = cur.fetchall()
print(f"\n=== adrg_procedure_map: 包含093.38的编码 (共{len(rows)}条) ===")
for r in rows[:50]:
    print(f"  {r[0]}")
if len(rows) > 50:
    print(f"  ... (还有{len(rows)-50}条)")

# Join query to see if any icd9_codes that are 物理-related have DRG mapping
cur.execute("""
    SELECT c.code, c.name, p.adrg_id
    FROM icd9_codes c
    LEFT JOIN adrg_procedure_map p ON p.icd9_code = c.code
    WHERE c.code LIKE '93.38%'
""")
print("\n=== icd9_codes 93.38* 是否有DRG映射 ===")
for r in cur.fetchall():
    print(f"  编码={r[0]}, 名称={r[1]}, adrg_id={r[2]}")

# Also try normalized join
cur.execute("""
    SELECT c.code, c.name, p.adrg_id
    FROM icd9_codes c
    LEFT JOIN adrg_procedure_map p ON p.icd9_code = '0' || c.code
    WHERE c.code LIKE '93.38%'
""")
print("\n=== icd9_codes 93.38* 前导零后是否有DRG映射 ===")
for r in cur.fetchall():
    print(f"  编码={r[0]}, 名称={r[1]}, adrg_id={r[2]}")

conn.close()
