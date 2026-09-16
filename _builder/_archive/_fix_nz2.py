import sqlite3
c=sqlite3.connect('icd_kb.db')
# Direct fix
c.execute("UPDATE drg_adrg SET name='女性生殖系统其他疾病' WHERE adrg_code='NZ1'")
c.commit()
r=c.execute("SELECT adrg_code, name FROM drg_adrg WHERE adrg_code='NZ1'").fetchone()
print('Result:', r)
c.close()
