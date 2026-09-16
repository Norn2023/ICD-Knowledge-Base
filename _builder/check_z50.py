import json, gzip, os
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with gzip.open(os.path.join(PROJ, '_builder/web/drg.json.gz'), 'rb') as f:
    d = json.loads(f.read().decode('utf-8'))

dx2a = d.get('dx2a', {})
print('Z50 diagnosis to ADRG mappings:')
for code in sorted(dx2a.keys()):
    if code.startswith('Z50'):
        for a in dx2a[code]:
            ac = a.get('a', '?')
            an = a.get('an', '(unnamed)')
            print(f'  {code} -> {ac} | {an}')

adrg_mdc = d.get('adrg_mdc', {})
print('\nXR ADRGs:')
for k in sorted(adrg_mdc.keys()):
    if k.startswith('XR'):
        v = adrg_mdc[k]
        print(f'  {k} | {v.get("mdc","?")} | {v.get("cat","?")} | {v.get("an","unnamed")}')

print('\nIZ ADRGs:')
for k in sorted(adrg_mdc.keys()):
    if k.startswith('IZ'):
        v = adrg_mdc[k]
        print(f'  {k} | {v.get("mdc","?")} | {v.get("cat","?")} | {v.get("an","unnamed")}')

# Also check how 93.xx codes are mapped - which table has them
px2a = d.get('px2a', {})
print('\n93.xx codes in px2a (top 10):')
count = 0
for code in sorted(px2a.keys()):
    if code.startswith('93.') and count < 10:
        adrgs = [(a.get('a','?'), a.get('an','?')) for a in px2a[code]]
        print(f'  {code} -> {adrgs}')
        count += 1

print(f'\nTotal 93.xx codes in px2a: {sum(1 for c in px2a if c.startswith("93."))}')
