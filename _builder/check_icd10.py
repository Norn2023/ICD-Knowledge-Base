import sqlite3
conn = sqlite3.connect("icd_kb.db")
cur = conn.cursor()
cur.execute("""
    SELECT COUNT(DISTINCT adm.icd10_code)
    FROM adrg_diagnosis_map adm
    LEFT JOIN icd10_codes ic ON adm.icd10_code = ic.code
    WHERE ic.code IS NULL AND adm.icd10_code NOT GLOB '[A-Z][A-Z][0-9]*'
""")
r = cur.fetchone()
print(f"非ADRG样式且不在icd10_codes的编码数: {r[0]}")
# Sample
cur.execute("""
    SELECT DISTINCT adm.icd10_code
    FROM adrg_diagnosis_map adm
    LEFT JOIN icd10_codes ic ON adm.icd10_code = ic.code
    WHERE ic.code IS NULL AND adm.icd10_code NOT GLOB '[A-Z][A-Z][0-9]*'
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r[0]}")
conn.close()
