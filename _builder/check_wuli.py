#!/usr/bin/env python3
"""Check '联合物理治疗' DRG mapping details"""
import sqlite3

conn = sqlite3.connect("icd_kb.db")
cur = conn.cursor()

# 1. icd9_codes 中物理治疗相关
print("=== icd9_codes 中物理治疗相关 ===")
cur.execute("SELECT code, name, icd9_3code FROM icd9_codes WHERE name LIKE '%物理%' OR name LIKE '%理疗%' OR code LIKE '93.38%'")
for r in cur.fetchall():
    print(f"  编码={r[0]}, 名称={r[1]}, 3位码={r[2]}")

# 2. icd9_clinical_map 中所有物理治疗相关
print()
print("=== icd9_clinical_map ===")
cur.execute("SELECT 医保编码, 医保名称, 国临版编码, 国临版名称 FROM icd9_clinical_map WHERE 医保名称 LIKE '%物理%' OR 国临版名称 LIKE '%物理%'")
for r in cur.fetchall():
    print(f"  医保编码={r[0]}, 医保名称={r[1]}, 国临版编码={r[2]}, 国临版名称={r[3]}")

# 3. adrg_procedure_map 中物理治疗相关
print()
print("=== adrg_procedure_map 中物理治疗相关 ===")
cur.execute("SELECT icd9_code, icd9_name, adrg_id, adrg_name, mdc_id FROM adrg_procedure_map WHERE icd9_name LIKE '%物理%' OR icd9_name LIKE '%理疗%'")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  icd9_code={r[0]}, icd9_name={r[1]}, adrg_id={r[2]}, adrg_name={r[3]}, mdc_id={r[4]}")
else:
    print("  (无结果)")

# 4. adrg_procedure_map 中 93.38 开头
print()
print("=== adrg_procedure_map 中 93.38* ===")
cur.execute("SELECT icd9_code, icd9_name, adrg_id, adrg_name FROM adrg_procedure_map WHERE icd9_code LIKE '93.38%'")
for r in cur.fetchall():
    print(f"  icd9_code={r[0]}, icd9_name={r[1]}, adrg_id={r[2]}, adrg_name={r[3]}")

# 5. 联合物理治疗相关编码在 adrg_procedure_map 中
print()
print("=== 尝试多种编码格式 ===")
for code in ['970301000', '34.08.001', '93.3800', '93.3800x001', '93.3800X001', '093.3800']:
    cur.execute("SELECT icd9_code, icd9_name, adrg_id, adrg_name FROM adrg_procedure_map WHERE icd9_code = ?", (code,))
    for r in cur.fetchall():
        print(f"  编码={code}: icd9_code={r[0]}, icd9_name={r[1]}, adrg_id={r[2]}, adrg_name={r[3]}")

# 6. 模糊搜索 adrg_procedure_map 中 93.38
print()
print("=== adrg_procedure_map 中 93.38 模糊搜索 ===")
cur.execute("SELECT icd9_code, icd9_name, adrg_id, adrg_name FROM adrg_procedure_map WHERE icd9_code LIKE '%93.38%' OR icd9_name LIKE '%93.38%'")
for r in cur.fetchall():
    print(f"  icd9_code={r[0]}, icd9_name={r[1]}, adrg_id={r[2]}, adrg_name={r[3]}")

# 7. all unique icd9_code patterns in adrg_procedure_map that might match
print()
print("=== adrg_procedure_map 中所有 93 开头编码 ===")
cur.execute("SELECT DISTINCT icd9_code, icd9_name FROM adrg_procedure_map WHERE icd9_code LIKE '93.%' OR icd9_code LIKE '093.%' ORDER BY icd9_code")
rows = cur.fetchall()
print(f"  共 {len(rows)} 条")
for r in rows[:20]:
    print(f"  {r[0]} | {r[1]}")
if len(rows) > 20:
    print(f"  ... (还有 {len(rows)-20} 条)")

conn.close()
