#!/usr/bin/env python3
"""Check DRG data sync issues"""
import sqlite3, json

DB_PATH = "icd_kb.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=" * 80)
print("1. 搜索 '联合物理治疗' 在 icd9_codes 中")
print("=" * 80)
rows = cur.execute("SELECT code, name FROM icd9_codes WHERE name LIKE '%联合物理治疗%' OR code LIKE '%联合物理治疗%'").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows:
    print(f"  {r['code']} | {r['name']}")

print()
print("=" * 80)
print("2. 搜索 '物理治疗' 在 icd9_codes 中")
print("=" * 80)
rows = cur.execute("SELECT code, name FROM icd9_codes WHERE name LIKE '%物理治疗%' OR code LIKE '%物理治疗%'").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows:
    print(f"  {r['code']} | {r['name']}")

print()
print("=" * 80)
print("3. 搜索 '物理治疗' 在 icd9_clinical_map 中")
print("=" * 80)
rows = cur.execute("SELECT yb_code, yb_name, clin_code, clin_name, category, entry_option FROM icd9_clinical_map WHERE yb_name LIKE '%物理治疗%' OR clin_name LIKE '%物理治疗%' OR yb_code LIKE '%物理治疗%' OR clin_code LIKE '%物理治疗%'").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows:
    print(f"  医保: {r['yb_code']} | {r['yb_name']}  --> 临床: {r['clin_code']} | {r['clin_name']}  [{r['category']}] [{r['entry_option']}]")

print()
print("=" * 80)
print("4. 搜索 '康复' 在 icd9_codes 中")
print("=" * 80)
rows = cur.execute("SELECT code, name FROM icd9_codes WHERE name LIKE '%康复%'").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows[:30]:
    print(f"  {r['code']} | {r['name']}")
if len(rows) > 30:
    print(f"  ... 还有 {len(rows)-30} 条")

print()
print("=" * 80)
print("5. DRG px2a 映射 - 检查所有包含'物理治疗'的映射")
print("=" * 80)
rows = cur.execute("""
    SELECT apm.icd9_code, ic.name as icd9_name, apm.adrg_id, a.adrg_code, a.name as adrg_name
    FROM adrg_procedure_map apm
    JOIN icd9_codes ic ON apm.icd9_code = ic.code
    JOIN drg_adrg a ON apm.adrg_id = a.id
    WHERE ic.name LIKE '%物理治疗%' OR apm.icd9_code LIKE '%物理治疗%'
""").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows:
    print(f"  手术: {r['icd9_code']} | {r['icd9_name']}  --> ADRG: {r['adrg_code']} | {r['adrg_name']}")

print()
print("=" * 80)
print("6. DRG px2a 映射 - 检查所有包含'康复'的映射")
print("=" * 80)
rows = cur.execute("""
    SELECT apm.icd9_code, ic.name as icd9_name, apm.adrg_id, a.adrg_code, a.name as adrg_name
    FROM adrg_procedure_map apm
    JOIN icd9_codes ic ON apm.icd9_code = ic.code
    JOIN drg_adrg a ON apm.adrg_id = a.id
    WHERE ic.name LIKE '%康复%'
""").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows[:30]:
    print(f"  手术: {r['icd9_code']} | {r['icd9_name']}  --> ADRG: {r['adrg_code']} | {r['adrg_name']}")
if len(rows) > 30:
    print(f"  ... 还有 {len(rows)-30} 条")

print()
print("=" * 80)
print("7. DRG px2a 总数 vs icd9_codes 总数")
print("=" * 80)
px_count = cur.execute("SELECT COUNT(*) FROM adrg_procedure_map").fetchone()[0]
icd9_count = cur.execute("SELECT COUNT(*) FROM icd9_codes").fetchone()[0]
px_in_drg = cur.execute("SELECT COUNT(DISTINCT icd9_code) FROM adrg_procedure_map").fetchone()[0]
px_not_in_drg = cur.execute("SELECT COUNT(*) FROM icd9_codes WHERE code NOT IN (SELECT DISTINCT icd9_code FROM adrg_procedure_map)").fetchone()[0]
print(f"ICD-9 手术编码总数: {icd9_count}")
print(f"ADRG 手术映射总数: {px_count}")
print(f"参与 DRG 映射的不同手术编码数: {px_in_drg}")
print(f"未参与 DRG 映射的手术编码数: {px_not_in_drg}")

print()
print("=" * 80)
print("8. DRG 分组表中存在但 icd9_codes 不存在的编码")
print("=" * 80)
rows = cur.execute("""
    SELECT DISTINCT apm.icd9_code
    FROM adrg_procedure_map apm
    LEFT JOIN icd9_codes ic ON apm.icd9_code = ic.code
    WHERE ic.code IS NULL
    ORDER BY apm.icd9_code
""").fetchall()
print(f"找到 {len(rows)} 个不在 icd9_codes 中的手术编码:")
for r in rows[:50]:
    print(f"  {r['icd9_code']}")
if len(rows) > 50:
    print(f"  ... 还有 {len(rows)-50} 个")

print()
print("=" * 80)
print("9. DRG 分组表中存在但 icd10_codes 不存在的编码")
print("=" * 80)
rows = cur.execute("""
    SELECT DISTINCT adm.icd10_code
    FROM adrg_diagnosis_map adm
    LEFT JOIN icd10_codes ic ON adm.icd10_code = ic.code
    WHERE ic.code IS NULL
    ORDER BY adm.icd10_code
""").fetchall()
print(f"找到 {len(rows)} 个不在 icd10_codes 中的诊断编码:")
for r in rows[:50]:
    print(f"  {r['icd10_code']}")
if len(rows) > 50:
    print(f"  ... 还有 {len(rows)-50} 个")

print()
print("=" * 80)
print("10. icd9_codes 存在但未映射到任何 DRG ADRG 的手术编码(前20)")
print("=" * 80)
total_unmapped = cur.execute("SELECT COUNT(*) FROM icd9_codes WHERE code NOT IN (SELECT DISTINCT icd9_code FROM adrg_procedure_map)").fetchone()[0]
rows = cur.execute("""
    SELECT ic.code, ic.name
    FROM icd9_codes ic
    LEFT JOIN adrg_procedure_map apm ON ic.code = apm.icd9_code
    WHERE apm.icd9_code IS NULL
    ORDER BY ic.code
    LIMIT 20
""").fetchall()
print(f"共 {total_unmapped} 个未映射")
for r in rows:
    print(f"  {r['code']} | {r['name']}")

print()
print("=" * 80)
print("11. icd10_codes 存在但未映射到任何 DRG ADRG 的诊断编码(前20)")
print("=" * 80)
total_unmapped_dx = cur.execute("SELECT COUNT(*) FROM icd10_codes WHERE code NOT IN (SELECT DISTINCT icd10_code FROM adrg_diagnosis_map)").fetchone()[0]
rows = cur.execute("""
    SELECT ic.code, ic.name
    FROM icd10_codes ic
    LEFT JOIN adrg_diagnosis_map adm ON ic.code = adm.icd10_code
    WHERE adm.icd10_code IS NULL
    ORDER BY ic.code
    LIMIT 20
""").fetchall()
print(f"共 {total_unmapped_dx} 个未映射")
for r in rows:
    print(f"  {r['code']} | {r['name']}")

print()
print("=" * 80)
print("12. 检查 icd9_codes 中的'物理治疗'相关编码详情")
print("=" * 80)
rows = cur.execute("SELECT code, name, chapter_id FROM icd9_codes WHERE name LIKE '%物理%' OR name LIKE '%理疗%'").fetchall()
print(f"找到 {len(rows)} 条:")
for r in rows:
    ch = cur.execute("SELECT name FROM icd9_chapters WHERE id=?", (r['chapter_id'],)).fetchone()
    print(f"  {r['code']} | {r['name']} | 章: {ch['name'] if ch else '?'}")

print()
print("=" * 80)
print("13. 检查 no_group_px 表")
print("=" * 80)
rows = cur.execute("SELECT icd9_code FROM no_group_px").fetchall()
print(f"不作为主手术的编码数: {len(rows)}")
phys_rows = [r for r in rows if '物理' in str(r)]
print(f"其中含'物理': {len(phys_rows)}")
for r in phys_rows:
    print(f"  {r['icd9_code']}")

conn.close()
