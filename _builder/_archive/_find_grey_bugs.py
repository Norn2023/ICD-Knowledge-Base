import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
c=sqlite3.connect('icd_kb.db'); cur=c.cursor()

# 1. Find codes in BOTH DB and clinical map (should NOT be grey)
print("=== Codes in BOTH icd10_codes AND clinical map ===")
cur.execute("SELECT COUNT(DISTINCT ic.code) FROM icd10_codes ic JOIN icd10_clinical_map cm ON ic.code=cm.yb_code")
print(f"  ICD-10 exact matches: {cur.fetchone()[0]}")

# 2. Find codes in DB with no EXACT clinical match (but maybe close)
cur.execute("""
  SELECT ic.code, ic.name FROM icd10_codes ic
  WHERE ic.code LIKE 'A04%'
  AND ic.code NOT IN (SELECT yb_code FROM icd10_clinical_map)
  LIMIT 10
""")
print("\n  ICD-10 A04 codes NOT in clinical map:")
for r in cur.fetchall():
    print(f"    {r[0]} {r[1][:60]}")

# 3. Check: are clinical map codes prefixed/suffixed differently?
cur.execute("""
  SELECT ic.code, ic.name, cm.yb_code, cm.clin_code
  FROM icd10_codes ic
  JOIN icd10_clinical_map cm ON ic.code||'x001'=cm.yb_code OR ic.code=cm.yb_code||'x001'
  WHERE ic.code LIKE 'A04%'
  LIMIT 5
""")
print("\n  ICD-10 A04 codes with x001 difference:")
for r in cur.fetchall():
    print(f"    DB:{r[0]} -> MAP:{r[2]} CLIN:{r[3]}")

# 4. Search for 艰难
print("\n=== 艰难梭菌 search ===")
cur.execute("SELECT code,name FROM icd10_codes WHERE name LIKE '%艰难%' OR name LIKE '%梭菌%'")
for r in cur.fetchall(): print(f"  ICD10 DB: {r[0]} {r[1][:60]}")
cur.execute("SELECT yb_code,clin_code,is_same FROM icd10_clinical_map WHERE yb_name LIKE '%艰难%' OR clin_name LIKE '%艰难%'")
for r in cur.fetchall(): print(f"  ICD10 MAP: YB={r[0]} CLIN={r[1]} same={r[2]}")

# 5. ICD-9 similar
cur.execute("SELECT code,name FROM icd9_codes WHERE name LIKE '%艰难%' OR name LIKE '%梭菌%'")
for r in cur.fetchall(): print(f"  ICD9 DB: {r[0]} {r[1][:60]}")
cur.execute("SELECT yb_code,clin_code,is_same FROM icd9_clinical_map WHERE yb_name LIKE '%艰难%' OR clin_name LIKE '%艰难%'")
for r in cur.fetchall(): print(f"  ICD9 MAP: YB={r[0]} CLIN={r[1]} same={r[2]}")

# 6. Global: how many ICD-10 grey codes are actually in the clinical map with a suffix diff?
cur.execute("""
  SELECT COUNT(*) FROM icd10_codes ic
  WHERE ic.code NOT IN (SELECT yb_code FROM icd10_clinical_map)
""")
total_grey = cur.fetchone()[0]
cur.execute("""
  SELECT COUNT(*) FROM icd10_codes ic
  WHERE ic.code NOT IN (SELECT yb_code FROM icd10_clinical_map)
  AND EXISTS (SELECT 1 FROM icd10_clinical_map cm WHERE cm.yb_code LIKE ic.code||'%' OR ic.code LIKE cm.yb_code||'%')
""")
fuzzy_match = cur.fetchone()[0]
print(f"\n  ICD-10 grey total: {total_grey}, could fuzzy-match: {fuzzy_match}")
