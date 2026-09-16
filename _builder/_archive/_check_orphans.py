import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
c=sqlite3.connect('icd_kb.db')
cur=c.cursor()

# Check whitespace
cur.execute("SELECT COUNT(*) FROM icd9_codes WHERE code != TRIM(code)")
print('Codes with whitespace:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM icd9_clinical_map WHERE yb_code != TRIM(yb_code)")
print('Clinical map YB with whitespace:', cur.fetchone()[0])

# Real orphans
cur.execute("""
  SELECT COUNT(DISTINCT TRIM(c.code)) FROM icd9_codes c
  WHERE TRIM(c.code) NOT IN (SELECT DISTINCT TRIM(yb_code) FROM icd9_clinical_map)
""")
print('Real orphans (trimmed):', cur.fetchone()[0])

# Sample mismatches
cur.execute("""
  SELECT DISTINCT TRIM(c.code) FROM icd9_codes c
  WHERE TRIM(c.code) NOT IN (SELECT DISTINCT TRIM(yb_code) FROM icd9_clinical_map)
  LIMIT 10
""")
print('Sample orphan codes:')
for (code,) in cur.fetchall():
    print(f'  {code}')

# Also check total unique
cur.execute("SELECT COUNT(DISTINCT TRIM(code)) FROM icd9_codes")
print('Total unique YB codes:', cur.fetchone()[0])
cur.execute("SELECT COUNT(DISTINCT TRIM(yb_code)) FROM icd9_clinical_map")
print('Total unique clinical YB codes:', cur.fetchone()[0])
