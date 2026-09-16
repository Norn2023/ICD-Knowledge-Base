import sqlite3
c=sqlite3.connect('icd_kb.db')
# DB
for row in c.execute("SELECT code,name FROM icd9_codes WHERE code LIKE '00.09%' OR code LIKE '0.09%'").fetchall():
    print('DB:', row[0], row[1][:50])
# Clinical map
for row in c.execute("SELECT yb_code,yb_name,clin_code,clin_name,is_same FROM icd9_clinical_map WHERE yb_code LIKE '00.09%' OR yb_code LIKE '0.09%'").fetchall():
    print('MAP: YB=', row[0], row[1][:40], '-> CLIN=', row[2], row[3][:40], 'same=', row[4])
