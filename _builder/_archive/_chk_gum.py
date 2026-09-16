import sqlite3, json
c=sqlite3.connect('icd_kb.db')
# Find gum biopsy code
r=c.execute("SELECT code,name FROM icd9_codes WHERE name LIKE '%牙龈%' OR name LIKE '%龈%'").fetchall()
print('DB gum codes:')
for row in r: print(f'  {row[0]} {row[1]}')

# Check in no_group_px
r2=c.execute("SELECT icd9_code FROM no_group_px").fetchall()
ng=set(x[0] for x in r2)
for row in r:
    print(f'  {row[0]} in no_px: {row[0] in ng}')

# Also check data.json
d=json.load(open('web/data.json','r',encoding='utf-8'))
ng2=set(d.get('no_px',[]))
for row in r:
    print(f'  {row[0]} in JSON no_px: {row[0] in ng2}')

c.close()
