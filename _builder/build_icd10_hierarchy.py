"""Extract ICD-10 hierarchy from original HTML import file: 类目, 亚目 info"""
import sqlite3, os, sys, pandas as pd, re
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
HTML_FILE = 'ICD-10医保2(2026年5月从医保局官网下载）.xlsx'

# Parse original HTML Excel for hierarchy
tables = pd.read_html(os.path.join(os.path.dirname(__file__), HTML_FILE))
df = tables[0]

# Columns from original file:
# 0: chapter_no, 1: chapter_range, 2: chapter_name
# 3: section_range, 4: section_name
# 5: cat_code, 6: cat_name
# 7: sub_code, 8: sub_name
# 9: diag_code, 10: diag_name
df.columns = ["ch_no","ch_range","ch_name","sec_range","sec_name",
              "cat_code","cat_name","sub_code","sub_name","code","name"]

data = df.iloc[1:].copy()
data = data.dropna(subset=["code"])
data['code'] = data.code.astype(str).str.strip()

print(f"Parsed {len(data)} rows from original file")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS icd10_hierarchy")
cur.execute("""
  CREATE TABLE icd10_hierarchy (
    code TEXT PRIMARY KEY,
    name TEXT,
    cat_code TEXT,
    cat_name TEXT,
    sub_code TEXT,
    sub_name TEXT,
    sec_range TEXT,
    sec_name TEXT,
    ch_range TEXT,
    ch_name TEXT,
    ch_no INTEGER
  )
""")

batch = []
for _, r in data.iterrows():
    code = str(r.code).strip()
    if not code or code == 'nan': continue
    batch.append((
        code,
        str(r.name)[:200] if pd.notna(r.name) else '',
        str(r.cat_code).strip() if pd.notna(r.cat_code) else '',
        str(r.cat_name)[:100] if pd.notna(r.cat_name) else '',
        str(r.sub_code).strip() if pd.notna(r.sub_code) else '',
        str(r.sub_name)[:100] if pd.notna(r.sub_name) else '',
        str(r.sec_range).strip() if pd.notna(r.sec_range) else '',
        str(r.sec_name)[:100] if pd.notna(r.sec_name) else '',
        str(r.ch_range).strip() if pd.notna(r.ch_range) else '',
        str(r.ch_name)[:100] if pd.notna(r.ch_name) else '',
        int(float(r.ch_no)) if pd.notna(r.ch_no) else 0
    ))
    if len(batch) >= 2000:
        cur.executemany("INSERT OR REPLACE INTO icd10_hierarchy VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
        conn.commit(); batch = []
if batch:
    cur.executemany("INSERT OR REPLACE INTO icd10_hierarchy VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
    conn.commit()

count = cur.execute("SELECT COUNT(*) FROM icd10_hierarchy").fetchone()[0]
print(f"Imported {count} codes with hierarchy")

# Sample
for r in cur.execute("SELECT * FROM icd10_hierarchy WHERE code='A00.000'").fetchall():
    print(f"\n  A00.000:")
    print(f"    类目: {r[2]} {r[3]}")
    print(f"    亚目: {r[4]} {r[5]}")
    print(f"    节:   {r[6]} {r[7]}")
    print(f"    章:   {r[8]} {r[9]} (第{r[10]}章)")

conn.close()
print("\nDone! Now update generate_web_json.py")
