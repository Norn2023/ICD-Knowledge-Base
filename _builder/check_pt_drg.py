import json, gzip, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(BASE)

# Load DRG data
with gzip.open(os.path.join(PROJ, '_builder/web/drg.json.gz'), 'rb') as f:
    drg = json.loads(f.read().decode('utf-8'))

# Load ICD-9 data for code names
with gzip.open(os.path.join(PROJ, '_builder/web/data.json.gz'), 'rb') as f:
    data = json.loads(f.read().decode('utf-8'))
icd9_map = {}
for c in data.get('icd9', []):
    icd9_map[c['c']] = c['n']

px2a = drg.get('px2a', {})
adrg_mdc = drg.get('adrg_mdc', {})

# Find physical therapy codes (93.xx)
pt_codes = []
for code in px2a:
    if code.startswith('93.'):
        pt_codes.append(code)

print(f'Total 93.xx codes in px2a: {len(pt_codes)}')
print()

# Group by ADRG
adrg_codes = {}
for code in pt_codes:
    for a in px2a[code]:
        ac = a.get('a', '?')
        if ac not in adrg_codes:
            adrg_codes[ac] = []
        adrg_codes[ac].append(code)

for ac in sorted(adrg_codes.keys()):
    v = adrg_mdc.get(ac, {})
    mdc = v.get('mdc', '?')
    cat = v.get('cat', '?')
    name = v.get('an', '(unnamed)')
    codes = adrg_codes[ac]
    # Print first 2 example codes with names
    examples = []
    for c in codes[:3]:
        n = icd9_map.get(c, '?')
        examples.append(c + ' ' + n)
    print(f'{ac} | {mdc} | {cat} | {name}')
    print(f'  count={len(codes)}, examples: {", ".join(examples)}')
    print()

# Also check if there are rehabilitation-specific concepts in MDC related to musculoskeletal/neurological
# MDCI (musculoskeletal), MDCB (nervous system)
print()
print('=== MDCI ADRGs ===')
for ac in sorted(adrg_mdc.keys()):
    v = adrg_mdc[ac]
    if v.get('mdc') == 'MDCI':
        print(f'{ac} | {v.get("cat","?")} | {v.get("an","(unnamed)")}')

print()
print('=== MDCB ADRGs ===')
for ac in sorted(adrg_mdc.keys()):
    v = adrg_mdc[ac]
    if v.get('mdc') == 'MDCB':
        print(f'{ac} | {v.get("cat","?")} | {v.get("an","(unnamed)")}')
