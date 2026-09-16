#!/usr/bin/env python3
"""
Merge procedure->ADRG mappings from 可编辑版's 手术ADRG sheet into the database.
"""
import sqlite3, os, sys, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
EXCEL = '0. CHS-DRG 2.0 表格可编辑版.xlsx'
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 60)
print("Step 1: Read 手术ADRG from 可编辑版")
print("=" * 60)

df = pd.read_excel(EXCEL, sheet_name='手术ADRG', engine='openpyxl', dtype=str)
print(f"Total rows: {len(df)}")

col_code = df.columns[0]  # 编码
col_name = df.columns[1]  # 名称
col_adrg = df.columns[2]  # ADRG编码
col_adrg_name = df.columns[6]  # ADRG名称

# Get existing mapping codes from DB
existing = set()
cur.execute("SELECT DISTINCT icd9_code FROM adrg_procedure_map")
for r in cur.fetchall():
    existing.add(r[0].strip())
print(f"Existing procedure codes in DB: {len(existing)}")

# Scan 可编辑版
editable_codes = set()
new_rows = []
missing_codes = []
adrg_cache = {}

for _, r in df.iterrows():
    code = str(r[col_code]).strip() if pd.notna(r[col_code]) else ''
    adrg = str(r[col_adrg]).strip() if pd.notna(r[col_adrg]) else ''
    adrg_name_val = str(r[col_adrg_name]).strip()[:200] if pd.notna(r[col_adrg_name]) else ''

    if not code or not adrg:
        continue

    editable_codes.add(code)

    if code in existing:
        continue

    # New mapping
    missing_codes.append(code)

    # Get/Create ADRG
    if adrg not in adrg_cache:
        cur.execute("SELECT id FROM drg_adrg WHERE adrg_code=?", (adrg,))
        row = cur.fetchone()
        if row:
            adrg_cache[adrg] = row[0]
        else:
            cur.execute("INSERT OR IGNORE INTO drg_adrg (adrg_code, name) VALUES (?,?)",
                       (adrg, adrg_name_val))
            cur.execute("SELECT id FROM drg_adrg WHERE adrg_code=?", (adrg,))
            row = cur.fetchone()
            if row:
                adrg_cache[adrg] = row[0]

    if adrg in adrg_cache:
        new_rows.append((adrg_cache[adrg], code))

print(f"Codes in 可编辑版 手术ADRG: {len(editable_codes)}")
print(f"New codes (not in DB): {len(missing_codes)}")
print(f"New mapping rows to insert: {len(new_rows)}")

# Show 93.38 specifics
print()
print("=" * 60)
print("93.38 codes analysis")
print("=" * 60)
for c in sorted(missing_codes):
    if c.startswith('93.38'):
        match = df[df[col_code] == c]
        if len(match) > 0:
            m = match.iloc[0]
            name_val = m[col_name] if pd.notna(m[col_name]) else ''
            adrg_val = m[col_adrg] if pd.notna(m[col_adrg]) else ''
            print(f"  {c} | {name_val} | ADRG: {adrg_val}")

# Also check existing 93.38 in DB
print()
cur.execute("""
    SELECT DISTINCT p.icd9_code 
    FROM adrg_procedure_map p 
    WHERE p.icd9_code LIKE '93.38%'
""")
existing_93 = [r[0] for r in cur.fetchall()]
print(f"93.38 codes already in DB: {len(existing_93)}")
for c in sorted(existing_93)[:10]:
    print(f"  {c}")

print()
if new_rows:
    cur.executemany("INSERT INTO adrg_procedure_map VALUES (?,?)", new_rows)
    conn.commit()
    print(f"Inserted {len(new_rows)} new procedure->ADRG mappings")
else:
    print("No new mappings to insert.")

# Final stats
cur.execute("SELECT COUNT(*) FROM adrg_procedure_map")
print(f"Total procedure maps: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(DISTINCT icd9_code) FROM adrg_procedure_map")
print(f"Distinct ICD-9 codes: {cur.fetchone()[0]}")

# Verify 93.38 again
cur.execute("""
    SELECT p.icd9_code, a.adrg_code, a.name
    FROM adrg_procedure_map p
    JOIN drg_adrg a ON p.adrg_id = a.id
    WHERE p.icd9_code LIKE '93.38%'
""")
rows = cur.fetchall()
print(f"93.38 mappings now: {len(rows)}")
for r in rows[:15]:
    print(f"  {r[0]} -> ADRG {r[1]} ({str(r[2])[:40]})")

conn.close()
print("Done!")
