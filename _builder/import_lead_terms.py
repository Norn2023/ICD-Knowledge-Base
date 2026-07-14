"""Import surgery lead terms (主导词)"""
import sqlite3, os, sys, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
df = pd.read_excel('手术主导词2025年11月29日修订少量错误.xlsx', engine='openpyxl')
df.columns = ['code', 'full_path', 'lead_term']

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS icd9_lead_terms")
cur.execute("CREATE TABLE icd9_lead_terms (code TEXT, full_path TEXT, lead_term TEXT)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_lead_code ON icd9_lead_terms(code)")

batch = []
for _, r in df.iterrows():
    code = str(r.code).strip() if pd.notna(r.code) else ''
    path = str(r.full_path) if pd.notna(r.full_path) else ''
    term = str(r.lead_term) if pd.notna(r.lead_term) else ''
    if code:
        batch.append((code, path[:500], term[:100]))
    if len(batch) >= 2000:
        cur.executemany("INSERT INTO icd9_lead_terms VALUES (?,?,?)", batch)
        conn.commit(); batch = []
if batch:
    cur.executemany("INSERT INTO icd9_lead_terms VALUES (?,?,?)", batch)
    conn.commit()

count = cur.execute("SELECT COUNT(*) FROM icd9_lead_terms").fetchone()[0]
unique = cur.execute("SELECT COUNT(DISTINCT code) FROM icd9_lead_terms").fetchone()[0]
print(f'Imported: {count} terms, {unique} unique codes')
print(f'Sample terms:')
for r in cur.execute("SELECT * FROM icd9_lead_terms WHERE code='47.09'").fetchall():
    print(f'  {r[0]} | {r[2]} | {r[1][:80]}')
conn.close()
