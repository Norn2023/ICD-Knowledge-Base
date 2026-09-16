import sqlite3
c=sqlite3.connect('icd_kb.db')
r=c.execute("SELECT adrg_code,name FROM drg_adrg WHERE adrg_code LIKE 'NZ%'").fetchall()
print(r)
# Also check the drg.json
import json
d=json.load(open('web/drg.json','r',encoding='utf-8'))
dx2a=d.get('dx2a',{})
for code,adrgs in dx2a.items():
    for a in adrgs:
        if a['a']=='NZ1':
            print(f"NZ1 name in drg.json: '{a['an']}'")
            break
    else: continue
    break
