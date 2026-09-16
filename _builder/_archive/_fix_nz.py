import sqlite3, pandas as pd
c=sqlite3.connect('icd_kb.db')

# Read the correct names from Excel
df=pd.read_excel('CHS-DRG2.0完整版.xlsx',sheet_name='ADRG',engine='openpyxl')
df.columns=['code','name']

# Re-import all ADRG names (there may be more bugs)
fixed=0
for _,r in df.iterrows():
    code=str(r.code).strip() if pd.notna(r.code) else ''
    name=str(r.name).strip() if pd.notna(r.name) else ''
    if code and code!='nan' and name and name!='nan':
        cur=c.execute("UPDATE drg_adrg SET name=? WHERE adrg_code=?",(name,code))
        if cur.rowcount>0: fixed+=1
c.commit()
print(f"Fixed {fixed} ADRG names")

# Verify NZ1
r=c.execute("SELECT name FROM drg_adrg WHERE adrg_code='NZ1'").fetchone()
print(f"NZ1 name: {r[0] if r else 'NOT FOUND'}")
c.close()
