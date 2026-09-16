"""Extract ICD-9 hierarchy from original HTML import file"""
import sqlite3, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
HTML_FILE = 'ICD-9-CM3医保2(2026年5月从医保局官网下载）.xlsx'

# Parse raw HTML (not pandas - it was mis-reading it)
with open(os.path.join(os.path.dirname(__file__), HTML_FILE), 'r', encoding='utf-8') as f:
    html = f.read()

# Extract all table rows
rows_raw = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.I)
print(f'HTML rows: {len(rows_raw)}')

parsed = []
for row_html in rows_raw:
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL | re.I)
    cleaned = []
    for c in cells:
        text = re.sub(r'<[^>]+>', '', c)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').strip()
        cleaned.append(text)
    parsed.append(cleaned)

# First row is header
header = parsed[0]
print(f'Header: {header}')

# Columns: 章, 章名称, 类目代码, 类目名称, 亚目代码, 亚目名称, 细目代码, 细目名称, 手术操作代码, 手术操作名称
data_rows = []
for row in parsed[1:]:
    if len(row) >= 10 and row[8].strip():  # has procedure code
        data_rows.append({
            'ch_no': row[0].strip(),
            'ch_name': row[1].strip(),
            'cat_code': row[2].strip(),
            'cat_name': row[3].strip(),
            'sub_code': row[4].strip(),
            'sub_name': row[5].strip(),
            'det_code': row[6].strip(),
            'det_name': row[7].strip(),
            'proc_code': row[8].strip(),
            'proc_name': row[9].strip()
        })

print(f'Data rows with procedure code: {len(data_rows)}')

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS icd9_hierarchy")
cur.execute("""
  CREATE TABLE icd9_hierarchy (
    code TEXT PRIMARY KEY,
    name TEXT,
    det_code TEXT, det_name TEXT,
    sub_code TEXT, sub_name TEXT,
    cat_code TEXT, cat_name TEXT,
    ch_no TEXT, ch_name TEXT
  )
""")

batch = []
for r in data_rows:
    batch.append((r['proc_code'], r['proc_name'][:200],
                  r['det_code'], r['det_name'][:100],
                  r['sub_code'], r['sub_name'][:100],
                  r['cat_code'], r['cat_name'][:100],
                  r['ch_no'], r['ch_name'][:100]))
    if len(batch) >= 2000:
        cur.executemany("INSERT OR REPLACE INTO icd9_hierarchy VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
        conn.commit(); batch = []
if batch:
    cur.executemany("INSERT OR REPLACE INTO icd9_hierarchy VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
    conn.commit()

count = cur.execute("SELECT COUNT(*) FROM icd9_hierarchy").fetchone()[0]
print(f'Imported {count} codes with hierarchy')

# Sample
for r in cur.execute("SELECT * FROM icd9_hierarchy WHERE code='47.0900'").fetchall():
    print(f'\n  47.0900:')
    print(f'    细目: {r[2]} {r[3]}')
    print(f'    亚目: {r[4]} {r[5]}')
    print(f'    类目: {r[6]} {r[7]}')
    print(f'    章:   {r[8]} {r[9]}')

conn.close()
print("\nDone!")
