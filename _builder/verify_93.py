#!/usr/bin/env python3
import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Check icd9_codes for 93.38
cur.execute("SELECT code, name FROM icd9_codes WHERE code LIKE '93.38%'")
rows = cur.fetchall()
print("93.38 codes in icd9_codes:", len(rows))
for r in rows:
    print(" ", r[0], "|", r[1])

# Check adrg_procedure_map for 93.38 (after our fix)
cur.execute("""
    SELECT DISTINCT p.icd9_code, a.adrg_code, a.name
    FROM adrg_procedure_map p
    JOIN drg_adrg a ON p.adrg_id = a.id
    WHERE p.icd9_code LIKE '93.38%'
    ORDER BY p.icd9_code, a.adrg_code
""")
rows2 = cur.fetchall()
print("\n93.38 in adrg_procedure_map:", len(rows2))
for r in rows2:
    print(" ", r[0], "->", r[1], "|", r[2][:50])

conn.close()
