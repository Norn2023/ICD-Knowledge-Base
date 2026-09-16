import json, gzip
import os; BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with gzip.open(os.path.join(BASE, '_builder/web/drg.json.gz'), 'rb') as f:
    d = json.loads(f.read().decode('utf-8'))

adrg_mdc = d.get('adrg_mdc', {})
print(f"Total ADRGs: {len(adrg_mdc)}")
for k in sorted(adrg_mdc.keys()):
    v = adrg_mdc[k]
    print(k + ' | ' + v.get('mdc', '?') + ' | ' + v.get('cat', '?') + ' | ' + v.get('an', '?'))

# Also check which ADRGs cover 93.xx physical therapy codes
px2a = d.get('px2a', {})
pt_codes = {}
for code in px2a:
    if code.startswith('93.'):
        for a in px2a[code]:
            adrg_code = a.get('a', '')
            if adrg_code not in pt_codes:
                pt_codes[adrg_code] = []
            pt_codes[adrg_code].append(code)

print(f"\n\nADRGs covering 93.xx physical therapy codes:")
for adrg in sorted(pt_codes.keys()):
    v = adrg_mdc.get(adrg, {})
    names = [a.get('an','') for a in px2a.get(pt_codes[adrg][0], [])]
    print(adrg + ' | ' + v.get('an', '?') + ' | count=' + str(len(pt_codes[adrg])))
