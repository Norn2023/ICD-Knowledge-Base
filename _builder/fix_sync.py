#!/usr/bin/env python3
"""Analyze and fix DRG data sync issues"""
import sqlite3, re

DB_PATH = "icd_kb.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 80)
print("【分析1】联合物理治疗 (93.3800x001) 在 DRG 映射中的情况")
print("=" * 80)
code = "93.3800x001"
row = cur.execute("SELECT code, name FROM icd9_codes WHERE code=?", (code,)).fetchone()
print(f"icd9_codes 中存在: {row is not None}")
if row: print(f"  {row['code']} | {row['name']}")

# Check in adrg_procedure_map
rows = cur.execute("""
    SELECT apm.icd9_code, a.adrg_code, a.name as adrg_name
    FROM adrg_procedure_map apm
    JOIN drg_adrg a ON apm.adrg_id = a.id
    WHERE apm.icd9_code = ?
""", (code,)).fetchall()
print(f"DRG 映射中存在: {len(rows)} 条")
for r in rows:
    print(f"  -> ADRG: {r['adrg_code']} | {r['adrg_name']}")

# Also check without x001
for try_code in ["93.38", "93.3800", "93.3801"]:
    rows = cur.execute("""
        SELECT apm.icd9_code, a.adrg_code, a.name as adrg_name
        FROM adrg_procedure_map apm
        JOIN drg_adrg a ON apm.adrg_id = a.id
        WHERE apm.icd9_code = ?
    """, (try_code,)).fetchall()
    if rows:
        print(f"\n相关编码 {try_code} 的 DRG 映射:")
        for r in rows:
            print(f"  -> ADRG: {r['adrg_code']} | {r['adrg_name']}")

# Check all 93.38* codes in icd9_codes and their DRG mapping
print("\n\n所有 93.38 相关编码的 DRG 映射情况:")
rows = cur.execute("""
    SELECT ic.code, ic.name, apm.icd9_code as mapped
    FROM icd9_codes ic
    LEFT JOIN adrg_procedure_map apm ON ic.code = apm.icd9_code
    WHERE ic.code LIKE '93.38%'
    ORDER BY ic.code
""").fetchall()
for r in rows:
    has_map = "有映射" if r['mapped'] else "无映射"
    print(f"  {r['code']} | {r['name']} -> {has_map}")

print()
print("=" * 80)
print("【分析2】adrg_procedure_map 中存在但 icd9_codes 不存的编码原因分析")
print("=" * 80)
rows = cur.execute("""
    SELECT DISTINCT apm.icd9_code, ic.code as actual_code, ic.name as actual_name
    FROM adrg_procedure_map apm
    LEFT JOIN icd9_codes ic ON apm.icd9_code = ic.code
    WHERE ic.code IS NULL
    ORDER BY apm.icd9_code
    LIMIT 30
""").fetchall()
print("前30条缺失编码:")
for r in rows:
    print(f"  {r['icd9_code']}")

# Check if they exist with different formatting (e.g. leading zeros stripped)
print("\n\n检查这些编码是否因格式不同而缺失:")
missing_codes = [r['icd9_code'] for r in rows]
for mc in missing_codes[:20]:
    # Try stripped leading zeros
    stripped = re.sub(r'^0+', '', mc) if mc.startswith('0') else None
    if stripped:
        found = cur.execute("SELECT code, name FROM icd9_codes WHERE code=?", (stripped,)).fetchone()
        if found:
            print(f"  {mc} -> 实际编码(去前导0): {found['code']}|{found['name']}")
            continue
    
    # Try without trailing zeros after decimal
    m = re.match(r'^(\d+)\.(\d+)$', mc)
    if m:
        whole = str(int(m.group(1)))
        frac = m.group(2).rstrip('0')
        if not frac: frac = '0'
        if frac != m.group(2):
            alt = f"{whole}.{frac}"
            found = cur.execute("SELECT code, name FROM icd9_codes WHERE code=?", (alt,)).fetchone()
            if found:
                print(f"  {mc} -> 实际编码(去尾部零): {found['code']}|{found['name']}")
                continue
    
    # Try without zeros at all
    m2 = re.match(r'^0*(\d+)\.(\d+)$', mc)
    if m2:
        alt2 = f"{m2.group(1)}.{m2.group(2)}"
        found = cur.execute("SELECT code, name FROM icd9_codes WHERE code=?", (alt2,)).fetchone()
        if found:
            print(f"  {mc} -> 实际编码(格式化): {found['code']}|{found['name']}")
            continue

print()
print("=" * 80)
print("【分析3】adrg_diagnosis_map 中存在但 icd10_codes 不存的编码")
print("=" * 80)
rows = cur.execute("""
    SELECT DISTINCT adm.icd10_code
    FROM adrg_diagnosis_map adm
    LEFT JOIN icd10_codes ic ON adm.icd10_code = ic.code
    WHERE ic.code IS NULL
    ORDER BY adm.icd10_code
    LIMIT 50
""").fetchall()
print(f"前50条:")
for r in rows:
    print(f"  {r['icd10_code']}")

print()
print("=" * 80)
print("【分析4】检查是否有康复/物理治疗类 ADRG")
print("=" * 80)
rows = cur.execute("""
    SELECT adrg_code, name, category, conditions
    FROM drg_adrg
    WHERE name LIKE '%康复%' OR name LIKE '%物理%' OR name LIKE '%理疗%'
""").fetchall()
print(f"找到 {len(rows)} 条")
for r in rows:
    print(f"  {r['adrg_code']} | {r['name']} | {r['category']}")

# Also check if there's any ADRG that physiotherapy might map to
print("\n检查手术操作类 ADRG (非手术室操作):")
rows = cur.execute("""
    SELECT adrg_code, name, category
    FROM drg_adrg
    WHERE category LIKE '%操作%' AND category NOT LIKE '%手术室%'
    LIMIT 20
""").fetchall()
for r in rows:
    print(f"  {r['adrg_code']} | {r['name']} | {r['category']}")

print()
print("=" * 80)
print("【结论汇总】")
print("=" * 80)

# 1. 联合物理治疗
px_count_37_39 = cur.execute("""
    SELECT COUNT(*) FROM icd9_codes 
    WHERE code LIKE '93.%' AND code IN (SELECT DISTINCT icd9_code FROM adrg_procedure_map)
""").fetchone()[0]
px_total_37_39 = cur.execute("""
    SELECT COUNT(*) FROM icd9_codes WHERE code LIKE '93.%'
""").fetchone()[0]
print(f"\n1. '联合物理治疗'(93.3800x001) 分析:")
print(f"   - icd9_codes 中第17章(物理治疗)编码: {px_total_37_39}个")
print(f"   - 其中已映射到 DRG ADRG: {px_count_37_39}个")
if px_count_37_39 == 0:
    print("   -> 整个第17章(物理治疗/康复)均未映射到任何DRG分组")
    print("   -> 这在 CHS-DRG 2.0 中是正常的，物理治疗属于康复类，")
    print("      通常不纳入 DRG 手术操作分组（属于内科治疗组）")

conn.close()
