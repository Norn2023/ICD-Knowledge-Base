"""Import CHS-DRG 2.0 complete version"""
import sqlite3, os, sys, pandas as pd, re, numpy as np
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
EXCEL = 'CHS-DRG2.0完整版.xlsx'
conn = sqlite3.connect(DB); cur = conn.cursor()

for t in ['drg_groups','drg_adrg','drg_mdc','adrg_diagnosis_map','adrg_procedure_map',
          'cc_exclusions','mcc_list','cc_list','no_group_dx','no_group_px']:
    cur.execute(f"DROP TABLE IF EXISTS {t}")

cur.executescript("""
  CREATE TABLE drg_mdc (id INTEGER PRIMARY KEY, mdc_code TEXT, name TEXT);
  CREATE TABLE drg_adrg (id INTEGER PRIMARY KEY, mdc_id INTEGER, adrg_code TEXT UNIQUE, name TEXT);
  CREATE TABLE drg_groups (id INTEGER PRIMARY KEY, adrg_id INTEGER, drg_code TEXT UNIQUE, name TEXT, severity TEXT DEFAULT 'unspecified');
  CREATE TABLE adrg_diagnosis_map (adrg_id INTEGER, icd10_code TEXT);
  CREATE TABLE adrg_procedure_map (adrg_id INTEGER, icd9_code TEXT);
  CREATE TABLE mcc_list (icd10_code TEXT, name TEXT, excluded TEXT);
  CREATE TABLE cc_list (icd10_code TEXT, name TEXT, excluded TEXT);
  CREATE TABLE cc_exclusions (table_name TEXT, icd10_code TEXT, name TEXT);
  CREATE TABLE no_group_dx (icd10_code TEXT, name TEXT);
  CREATE TABLE no_group_px (icd9_code TEXT, name TEXT);
""")

# ═══ 1. ADRG ═══
df_adrg = pd.read_excel(EXCEL, sheet_name='ADRG', engine='openpyxl')
df_adrg.columns = ['code','name']
adrg_ids = {}
for _, r in df_adrg.iterrows():
    c = str(r.code).strip() if pd.notna(r.code) else ''
    if c and c != 'nan':
        cur.execute("INSERT INTO drg_adrg (adrg_code, name) VALUES (?,?)", (c, str(r.name).strip()[:200]))
        adrg_ids[c] = cur.lastrowid
conn.commit()
print(f"ADRGs: {len(adrg_ids)}")

# ═══ 2. DRG组 ═══
df_drg = pd.read_excel(EXCEL, sheet_name='DRG组', engine='openpyxl')
df_drg.columns = ['seq','adrg_code','drg_code','drg_name']
drg_count = 0
for _, r in df_drg.iterrows():
    adrg = str(r.adrg_code).strip() if pd.notna(r.adrg_code) else ''
    drg = str(r.drg_code).strip() if pd.notna(r.drg_code) else ''
    name = str(r.drg_name).strip() if pd.notna(r.drg_name) else ''
    sev = 'unspecified'
    if '严重' in name: sev = 'MCC'
    elif name and '一般' in name and '合并' in name: sev = 'CC'
    elif '不伴' in name: sev = 'noCC'
    if adrg in adrg_ids and drg and drg != 'nan':
        cur.execute("INSERT OR IGNORE INTO drg_groups (adrg_id, drg_code, name, severity) VALUES (?,?,?,?)",
                   (adrg_ids[adrg], drg, name, sev)); drg_count += 1
conn.commit()
print(f"DRG groups: {drg_count}")

# ═══ 3. 入组条件 (diagnosis + procedure → ADRG) ═══
df_cond = pd.read_excel(EXCEL, sheet_name='入组条件', engine='openpyxl')
df_cond.columns = ['mdc','adrg','code','name','u4','u5']
cur_adrg = None; in_proc = False; dx_batch = []; px_batch = []
for _, r in df_cond.iterrows():
    adrg = str(r.adrg).strip() if pd.notna(r.adrg) else ''
    code = str(r.code).strip() if pd.notna(r.code) else ''
    if adrg in adrg_ids: cur_adrg = adrg_ids[adrg]; in_proc = False
    if cur_adrg and code and code != 'nan':
        if '包含以下主要手术' in code or '主要手术或操作' in code:
            in_proc = True
        elif '包含以下主要诊断' in code:
            in_proc = False
        elif re.match(r'^[A-Z]', code):
            dx_batch.append((cur_adrg, code))
        elif re.match(r'^\d', code):
            px_batch.append((cur_adrg, code))
    if len(dx_batch) >= 5000: cur.executemany("INSERT INTO adrg_diagnosis_map VALUES (?,?)", dx_batch); conn.commit(); dx_batch = []
    if len(px_batch) >= 5000: cur.executemany("INSERT INTO adrg_procedure_map VALUES (?,?)", px_batch); conn.commit(); px_batch = []
if dx_batch: cur.executemany("INSERT INTO adrg_diagnosis_map VALUES (?,?)", dx_batch); conn.commit()
if px_batch: cur.executemany("INSERT INTO adrg_procedure_map VALUES (?,?)", px_batch); conn.commit()
print(f"Diagnosis maps: {cur.execute('SELECT COUNT(*) FROM adrg_diagnosis_map').fetchone()[0]}")
print(f"Procedure maps: {cur.execute('SELECT COUNT(*) FROM adrg_procedure_map').fetchone()[0]}")

# ═══ 4. MCC ═══
df_mcc = pd.read_excel(EXCEL, sheet_name='MCC', engine='openpyxl')
df_mcc.columns = ['seq','code','name','excluded']
mcc_batch = []
for _, r in df_mcc.iterrows():
    c = str(r.code).strip() if pd.notna(r.code) else ''
    if c and c != 'nan': mcc_batch.append((c, str(r.name).strip()[:200], str(r.excluded).strip() if pd.notna(r.excluded) else ''))
cur.executemany("INSERT OR IGNORE INTO mcc_list VALUES (?,?,?)", mcc_batch); conn.commit()
print(f"MCC codes: {len(mcc_batch)}")

# ═══ 5. CC ═══
df_cc = pd.read_excel(EXCEL, sheet_name='CC', engine='openpyxl')
df_cc.columns = ['seq','code','name','excluded']
cc_batch = []
for _, r in df_cc.iterrows():
    c = str(r.code).strip() if pd.notna(r.code) else ''
    if c and c != 'nan': cc_batch.append((c, str(r.name).strip()[:200], str(r.excluded).strip() if pd.notna(r.excluded) else ''))
cur.executemany("INSERT OR IGNORE INTO cc_list VALUES (?,?,?)", cc_batch); conn.commit()
print(f"CC codes: {len(cc_batch)}")

# ═══ 6. 排除表 ═══
df_excl = pd.read_excel(EXCEL, sheet_name='排除表', engine='openpyxl')
df_excl.columns = ['seq','table','code','name']
excl_batch = []
for _, r in df_excl.iterrows():
    c = str(r.code).strip() if pd.notna(r.code) else ''
    if c and c != 'nan': excl_batch.append((str(r.table).strip(), c, str(r.name).strip()[:200]))
cur.executemany("INSERT INTO cc_exclusions VALUES (?,?,?)", excl_batch); conn.commit()
print(f"Exclusion records: {len(excl_batch)}")

# ═══ 7. 不作为主诊 ═══
df_ndx = pd.read_excel(EXCEL, sheet_name='不作为主诊', engine='openpyxl')
ndx_batch = []
for _, r in df_ndx.iterrows():
    c = str(r.iloc[1]).strip() if pd.notna(r.iloc[1]) else ''
    if c and c != 'nan': ndx_batch.append((c, str(r.iloc[2]).strip()[:200] if len(r)>2 else ''))
cur.executemany("INSERT INTO no_group_dx VALUES (?,?)", ndx_batch); conn.commit()
print(f"Non-grouping diagnoses: {len(ndx_batch)}")

# ═══ 8. 不作为主手术 ═══
df_npx = pd.read_excel(EXCEL, sheet_name='不作为主手术', engine='openpyxl')
npx_batch = []
for _, r in df_npx.iterrows():
    c = str(r.iloc[1]).strip() if pd.notna(r.iloc[1]) else ''
    if c and c != 'nan': npx_batch.append((c, str(r.iloc[2]).strip()[:200] if len(r)>2 else ''))
cur.executemany("INSERT INTO no_group_px VALUES (?,?)", npx_batch); conn.commit()
print(f"Non-grouping procedures: {len(npx_batch)}")

# Stats
print(f"\n=== Final ===")
for t in ['drg_adrg','drg_groups','adrg_diagnosis_map','adrg_procedure_map','mcc_list','cc_list','cc_exclusions','no_group_dx','no_group_px']:
    print(f"  {t}: {cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
conn.close()
print("\nDone!")
