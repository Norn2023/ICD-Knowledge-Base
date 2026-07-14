"""Import clinical 2.0 (国临版) vs insurance 2.0 (医保版) complete mapping"""
import sqlite3, os, sys, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
EXCEL = 'ICD10国临版2.0对照医保版2.0.xlsx'

df = pd.read_excel(os.path.join(os.path.dirname(__file__), EXCEL), engine='openpyxl')
df.columns = ['clin_code', 'clin_name', 'yb_code', 'yb_name', 'same']

df['clin_code'] = df.clin_code.astype(str).str.strip()
df['yb_code'] = df.yb_code.astype(str).str.strip()
df['same'] = df.same.fillna(0).astype(int)

print(f'Rows: {len(df)}, Clinical unique: {df.clin_code.nunique()}, YB unique: {df.yb_code.nunique()}')
print(f'Same: {(df.same==1).sum()}, Different: {(df.same!=1).sum()}')

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS icd10_clinical_map")
cur.execute("""
  CREATE TABLE icd10_clinical_map (
    id INTEGER PRIMARY KEY,
    clin_code TEXT NOT NULL,
    clin_name TEXT,
    yb_code TEXT NOT NULL,
    yb_name TEXT,
    is_same INTEGER DEFAULT 1
  )
""")

batch = []
for _, r in df.iterrows():
    batch.append((r.clin_code, str(r.clin_name)[:200] if pd.notna(r.clin_name) else '',
                   r.yb_code, str(r.yb_name)[:200] if pd.notna(r.yb_name) else '', r.same))
    if len(batch) >= 2000:
        cur.executemany("INSERT INTO icd10_clinical_map (clin_code,clin_name,yb_code,yb_name,is_same) VALUES (?,?,?,?,?)", batch)
        conn.commit(); batch = []

if batch:
    cur.executemany("INSERT INTO icd10_clinical_map (clin_code,clin_name,yb_code,yb_name,is_same) VALUES (?,?,?,?,?)", batch)
    conn.commit()

cur.execute("CREATE INDEX IF NOT EXISTS idx_clin20_c ON icd10_clinical_map(clin_code)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_clin20_y ON icd10_clinical_map(yb_code)")

# Check matches to main DB
in_db = cur.execute("""
  SELECT COUNT(*) FROM icd10_clinical_map cm
  WHERE cm.yb_code IN (SELECT code FROM icd10_codes)
""").fetchone()[0]
print(f'YB codes in DB: {in_db}/{len(df)}')

# YB codes in DB but NOT in clinical map (grey candidates)
orphans = cur.execute("""
  SELECT COUNT(*) FROM icd10_codes c
  WHERE c.code NOT IN (SELECT DISTINCT yb_code FROM icd10_clinical_map)
""").fetchone()[0]
print(f'医保码无临床对应(灰标): {orphans}')

count = cur.execute("SELECT COUNT(*) FROM icd10_clinical_map").fetchone()[0]
print(f'Imported: {count}')
conn.close()
