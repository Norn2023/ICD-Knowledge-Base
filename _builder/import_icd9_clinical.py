"""Import ICD-9 clinical 3.0 mapping + category/entry/drg info"""
import sqlite3, os, sys, pandas as pd, numpy as np
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
DIR = os.path.dirname(__file__)

# File 1: clinical↔insurance mapping
print("=== File 1: ICD9 mapping ===")
df1 = pd.read_excel(os.path.join(DIR, 'ICD9国临版3.0对照医保版2.0_0125.xlsx'), engine='openpyxl')
df1.columns = ['clin_code','clin_name','yb_code','yb_name','same','exclude_drg']
df1['clin_code'] = df1.clin_code.astype(str).str.strip()
df1['yb_code'] = df1.yb_code.astype(str).str.strip()
df1['same'] = df1.same.fillna(0).astype(int)
df1['exclude_drg'] = df1.exclude_drg.fillna(0).astype(int)

print(f'  Rows: {len(df1)}, Clinical: {df1.clin_code.nunique()}, YB: {df1.yb_code.nunique()}')
print(f'  Same: {(df1.same==1).sum()}, Different: {(df1.same!=1).sum()}')
print(f'  DRG excluded: {df1.exclude_drg.sum()}')

# File 2: clinical 3.0 with category/entry
print("\n=== File 2: ICD9 clinical 3.0 categories ===")
df2 = pd.read_excel(os.path.join(DIR, '手术操作分类代码国家临床版3.0（2022汇总版）.xlsx'), engine='openpyxl')
df2.columns = ['main_code','extra_code','name','category','entry_option']
df2['main_code'] = df2.main_code.astype(str).str.strip()
print(f'  Rows: {len(df2)}, Codes: {df2.main_code.nunique()}')
print(f'  Categories: {df2.category.value_counts().to_dict()}')
print(f'  Entry options: {df2.entry_option.value_counts().to_dict()}')

# Merge: clinical code from df1 with df2 categories
df2_dict = {}
for _, r in df2.iterrows():
    code = r.main_code
    if code and code != 'nan':
        df2_dict[code] = {
            'name': str(r.name) if pd.notna(r.name) else '',
            'category': str(r.category) if pd.notna(r.category) else '',
            'entry': str(r.entry_option) if pd.notna(r.entry_option) else ''
        }

# Now create merged data
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS icd9_clinical_map")
cur.execute("""
  CREATE TABLE icd9_clinical_map (
    id INTEGER PRIMARY KEY,
    clin_code TEXT NOT NULL,
    clin_name TEXT,
    yb_code TEXT NOT NULL,
    yb_name TEXT,
    is_same INTEGER DEFAULT 1,
    exclude_drg INTEGER DEFAULT 0,
    category TEXT,
    entry_option TEXT,
    clin30_name TEXT
  )
""")

batch, stats = [], {'same':0,'diff':0,'drg_excl':0,'grey':0,'cats':{}}

for _, r in df1.iterrows():
    cc = r.clin_code
    info = df2_dict.get(cc, {})
    cat = info.get('category', '')
    entry = info.get('entry', '')
    is_grey = (r.same != 1)

    batch.append((cc, str(r.clin_name)[:200] if pd.notna(r.clin_name) else '',
                   r.yb_code, str(r.yb_name)[:200] if pd.notna(r.yb_name) else '',
                   r.same, r.exclude_drg, cat, entry, info.get('name', '')))

    if r.same == 1: stats['same'] += 1
    else: stats['diff'] += 1
    if r.exclude_drg: stats['drg_excl'] += 1
    if is_grey: stats['grey'] += 1
    if cat: stats['cats'][cat] = stats['cats'].get(cat, 0) + 1

    if len(batch) >= 2000:
        cur.executemany("INSERT INTO icd9_clinical_map (clin_code,clin_name,yb_code,yb_name,is_same,exclude_drg,category,entry_option,clin30_name) VALUES (?,?,?,?,?,?,?,?,?)", batch)
        conn.commit(); batch = []
if batch:
    cur.executemany("INSERT INTO icd9_clinical_map (clin_code,clin_name,yb_code,yb_name,is_same,exclude_drg,category,entry_option,clin30_name) VALUES (?,?,?,?,?,?,?,?,?)", batch)
    conn.commit()

cur.execute("CREATE INDEX IF NOT EXISTS idx_icd9clin_c ON icd9_clinical_map(clin_code)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_icd9clin_y ON icd9_clinical_map(yb_code)")

# Check YB codes not in clinical map
orphans = cur.execute("""
  SELECT COUNT(*) FROM icd9_codes c
  WHERE c.code NOT IN (SELECT DISTINCT yb_code FROM icd9_clinical_map)
""").fetchone()[0]
stats['grey'] += orphans

count = cur.execute("SELECT COUNT(*) FROM icd9_clinical_map").fetchone()[0]
print(f"\nImported: {count}")
print(f"  Same: {stats['same']}")
print(f"  Different (grey): {stats['diff']}")
print(f"  DRG excluded: {stats['drg_excl']}")
print(f"  YB orphans (grey): {orphans}")
print(f"  Categories: {stats['cats']}")
conn.close()
print("\nDone!")
