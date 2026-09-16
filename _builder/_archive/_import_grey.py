"""Import grey codes and add to drg.json"""
import sqlite3, json, pandas as pd, sys, os
sys.stdout.reconfigure(encoding='utf-8')

c = sqlite3.connect('icd_kb.db')
cur = c.cursor()

# Read grey codes from CHS-DRG Excel
grey1 = pd.read_excel('CHS-DRG2.0完整版.xlsx', sheet_name='灰码', engine='openpyxl')
grey2 = pd.read_excel('CHS-DRG2.0完整版.xlsx', sheet_name='灰码2', engine='openpyxl')

# Collect grey codes
grey_set = set()

# Sheet 灰码: 国临2.0诊断编码, 国临2.0诊断名称, 标准诊断编码-医保版2.0, ...
grey1.columns = ['clin','cname','yb','yname','mark','note']
for _, r in grey1.iterrows():
    yb = str(r.yb).strip() if pd.notna(r.yb) else ''
    clin = str(r.clin).strip() if pd.notna(r.clin) else ''
    if yb and yb != 'nan': grey_set.add(yb)
    if clin and clin != 'nan': grey_set.add(clin)

# Sheet 灰码2
grey2.columns = ['code','u1','mark','note']
for _, r in grey2.iterrows():
    code = str(r.code).strip() if pd.notna(r.code) else ''
    if code and code != 'nan': grey_set.add(code)

print(f"Grey codes collected: {len(grey_set)}")

# Also identify 未特指 (unspecified) codes
# Pattern: codes ending with .9, .x00, .900, etc.
# We'll mark these in the frontend based on code pattern
# Common patterns: Xxx.9, Xxx.x00, Xxx.900

# Save to JSON
grey_list = sorted(list(grey_set))

# Update drg.json
with open('web/drg.json', 'r', encoding='utf-8') as f:
    drg = json.load(f)

drg['grey'] = grey_list
# Also add unspecified code patterns for the frontend
drg['unspec_patterns'] = [r'\.9$', r'\.9\d*$', r'\.x00$', r'\.900$']

with open('web/drg.json', 'w', encoding='utf-8') as f:
    json.dump(drg, f, ensure_ascii=False)

print(f"drg.json updated with {len(grey_list)} grey codes")
