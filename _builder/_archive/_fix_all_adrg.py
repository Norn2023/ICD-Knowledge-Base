import sqlite3, pandas as pd
c = sqlite3.connect('icd_kb.db')

df = pd.read_excel('CHS-DRG2.0完整版.xlsx', sheet_name='ADRG', engine='openpyxl')

fixed = 0
for i, r in df.iterrows():
    code = str(df.iloc[i, 0]).strip()
    name = str(df.iloc[i, 1]).strip()
    if code and code != 'nan' and name and name != 'nan':
        c.execute("UPDATE drg_adrg SET name=? WHERE adrg_code=?", (name, code))
        fixed += 1

c.commit()
print(f"Updated {fixed} ADRGs")

# Verify problem codes
for code in ['NZ1', 'NA2', 'NC1', 'OD1', 'AA1', 'BR1', 'FR1']:
    r = c.execute("SELECT adrg_code, name FROM drg_adrg WHERE adrg_code=?", (code,)).fetchone()
    print(f"  {r[0]}: {r[1][:50] if r else 'NOT FOUND'}")

c.close()
