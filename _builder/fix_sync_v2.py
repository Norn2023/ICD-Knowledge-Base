#!/usr/bin/env python3
"""Verify mismatch causes and fix them"""
import sqlite3, re

DB_PATH = "icd_kb.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check remaining missing codes pattern
print("仍然缺失的编码示例及分析:")
cur.execute("""
    SELECT DISTINCT apm.icd9_code
    FROM adrg_procedure_map apm
    LEFT JOIN icd9_codes ic ON apm.icd9_code = ic.code
    WHERE ic.code IS NULL
    ORDER BY apm.icd9_code
""")
all_missing = [r['icd9_code'] for r in cur.fetchall()]

# Normalize: remove leading zeros
def normalize_leading(code):
    m = re.match(r'^0*(\d+)\.(.+)$', code)
    if m: return f"{m.group(1)}.{m.group(2)}"
    return code

# Normalize: strip trailing zeros after decimal
def normalize_trailing(code):
    m = re.match(r'^(\d+)\.(\d+?)0*$', code)
    if m:
        frac = m.group(2)
        return f"{m.group(1)}.{frac}"
    return code

matched = 0
still_missing = []
for code in all_missing:
    n1 = normalize_leading(code)
    n2 = normalize_trailing(code)
    found = cur.execute("SELECT code, name FROM icd9_codes WHERE code=? OR code=?", (n1, n2)).fetchone()
    if found:
        matched += 1
        # print(f"  {code} -> {found['code']} | {found['name']}")
    else:
        still_missing.append(code)

print(f"前导零盘正后可匹配: {matched} 个")
print(f"仍然缺失: {len(still_missing)} 个")
print("仍然缺失的示例:")
for c in still_missing[:20]:
    print(f"  {c}")

# Check patterns
print("\n\n第17章(物理治疗)已有DRG映射的编码:")
cur.execute("""
    SELECT ic.code, ic.name, a.adrg_code, a.name as adrg_name
    FROM icd9_codes ic
    JOIN adrg_procedure_map apm ON ic.code = apm.icd9_code
    JOIN drg_adrg a ON apm.adrg_id = a.id
    WHERE ic.code LIKE '93.%'
""")
rows = cur.fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows:
    print(f"  {r['code']} | {r['name']} -> ADRG {r['adrg_code']} | {r['adrg_name']}")

# Also check 89.37
print("\n其它康复相关编码的DRG映射:")
cur.execute("""
    SELECT ic.code, ic.name, a.adrg_code, a.name as adrg_name
    FROM icd9_codes ic
    JOIN adrg_procedure_map apm ON ic.code = apm.icd9_code
    JOIN drg_adrg a ON apm.adrg_id = a.id
    WHERE ic.name LIKE '%康复%' OR ic.name LIKE '%物理治疗%'
""")
rows = cur.fetchall()
for r in rows:
    print(f"  {r['code']} | {r['name']} -> ADRG {r['adrg_code']} | {r['adrg_name']}")

# ADRG codes in diagnosis map
print("\n\n诊断映射表中ADRG编码样式的条目:")
cur.execute("""
    SELECT DISTINCT adm.icd10_code
    FROM adrg_diagnosis_map adm
    LEFT JOIN icd10_codes ic ON adm.icd10_code = ic.code
    WHERE ic.code IS NULL AND adm.icd10_code GLOB '[A-Z][A-Z][0-9]*'
    ORDER BY adm.icd10_code
""")
rows = cur.fetchall()
print(f"  ADRG编码样式的条目: {len(rows)} 个")
for r in rows[:5]:
    print(f"    {r['icd10_code']}")

conn.close()
