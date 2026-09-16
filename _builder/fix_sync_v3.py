#!/usr/bin/env python3
"""Detailed check of remaining missing codes"""
import sqlite3, re

DB_PATH = "icd_kb.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Advanced normalization
def normalize_full(code):
    # Remove leading zeros from whole part
    m = re.match(r'^0*(\d+)\.(.+)$', code)
    if m:
        whole = m.group(1)
        rest = m.group(2)
        # Remove trailing zeros from decimal part (but keep at least one digit)
        rest = rest.rstrip('0')
        if not rest: rest = '0'
        return f"{whole}.{rest}"
    code = code.lstrip('0')
    if not code: return '0'
    return code

# Check remaining missing
cur.execute("""
    SELECT DISTINCT apm.icd9_code
    FROM adrg_procedure_map apm
    LEFT JOIN icd9_codes ic ON apm.icd9_code = ic.code
    WHERE ic.code IS NULL
    ORDER BY apm.icd9_code
""")
all_missing = [r[0] for r in cur.fetchall()]

matched = 0
still_missing = []
for code in all_missing:
    norm = normalize_full(code)
    found = cur.execute("SELECT code, name FROM icd9_codes WHERE code=?", (norm,)).fetchone()
    if found:
        matched += 1
        # Verify name matches clinical map
        clin = cur.execute("SELECT yb_name FROM icd9_clinical_map WHERE yb_code=? LIMIT 1", (code,)).fetchone()
        clin_name = clin[0] if clin else '?'
        if matched <= 5:
            print(f"  匹配: {code} -> {found[1]} (临床名: {clin_name})")
    else:
        still_missing.append(code)

print(f"\n高级格式化后可匹配: {matched} 个")
print(f"仍然缺失: {len(still_missing)} 个")

# Check if remaining ones exist in icd9_clinical_map
print("\n仍然缺失编码在临床映射表中:")
for c in still_missing[:30]:
    clin = cur.execute("SELECT yb_code, yb_name, clin_code, clin_name FROM icd9_clinical_map WHERE yb_code=? LIMIT 1", (c,)).fetchone()
    if clin:
        print(f"  医保: {clin[0]} | {clin[1]} -> 临床: {clin[2]} | {clin[3]}")
    else:
        print(f"  {c} - 也不在临床映射表中")

conn.close()
