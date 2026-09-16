#!/usr/bin/env python3
"""Clean up ADRG codes mistakenly stored in adrg_diagnosis_map"""
import sqlite3, re

DB_PATH = "icd_kb.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find entries where icd10_code looks like an ADRG code (e.g. AA1, AB1, AA100)
print("分析 adrg_diagnosis_map 中的 ADRG 样式编码:")
cur.execute("""
    SELECT adm.icd10_code, a.adrg_code, a.name as adrg_name
    FROM adrg_diagnosis_map adm
    JOIN drg_adrg a ON adm.adrg_id = a.id
    WHERE adm.icd10_code GLOB '[A-Z][A-Z][0-9]*'
    ORDER BY adm.icd10_code
    LIMIT 20
""")
print("前20条示例:")
for r in cur.fetchall():
    print(f"  icd10_code字段='{r['icd10_code']}' -> ADRG {r['adrg_code']} | {r['adrg_name']}")

# Count them
cur.execute("""
    SELECT COUNT(*) 
    FROM adrg_diagnosis_map 
    WHERE icd10_code GLOB '[A-Z][A-Z][0-9]*'
""")
total = cur.fetchone()[0]
print(f"\n共 {total} 条需要删除的ADRG编码条目")

# Check which ADRGs they belong to
cur.execute("""
    SELECT a.adrg_code, a.name, COUNT(*) as cnt
    FROM adrg_diagnosis_map adm
    JOIN drg_adrg a ON adm.adrg_id = a.id
    WHERE adm.icd10_code GLOB '[A-Z][A-Z][0-9]*'
    GROUP BY a.adrg_code
    ORDER BY cnt DESC
    LIMIT 10
""")
print("按ADRG分组:")
for r in cur.fetchall():
    print(f"  ADRG {r['adrg_code']} | {r['name']}: {r['cnt']}条")

# Show one example to understand the structure
print("\n第一条数据的完整记录:")
cur.execute("""
    SELECT * FROM adrg_diagnosis_map
    WHERE icd10_code GLOB '[A-Z][A-Z][0-9]*'
    LIMIT 1
""")
r = cur.fetchone()
if r:
    for k in r.keys():
        print(f"  {k}: {r[k]}")

# Now delete them
print(f"\n删除 {total} 条ADRG编码...")
cur.execute("""
    DELETE FROM adrg_diagnosis_map 
    WHERE icd10_code GLOB '[A-Z][A-Z][0-9]*'
""")
conn.commit()
print("删除完成")

# Verify
cur.execute("SELECT COUNT(*) FROM adrg_diagnosis_map")
remaining = cur.fetchone()[0]
print(f"adrg_diagnosis_map 剩余条目: {remaining}")

conn.close()
