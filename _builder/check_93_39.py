import json, gzip, os
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with gzip.open(os.path.join(PROJ, '_builder/web/drg.json.gz'), 'rb') as f:
    d = json.loads(f.read().decode('utf-8'))

px2a = d.get('px2a', {})

# Specific physical therapy codes
targets = ['93.39', '93.3900x001', '93.3900x003', '17.97410', '17.97500', '17.9211']
for code in targets:
    if code in px2a:
        for a in px2a[code]:
            print(code + ' -> ' + a.get('a','?') + ' | ' + a.get('an','?'))
    else:
        print(code + ': NOT IN px2a')

# Chinese physical therapy codes 17.9x
print('\n17.9x codes in px2a:')
count = 0
for code in sorted(px2a.keys()):
    if code.startswith('17.9'):
        for a in px2a[code]:
            print(code + ' -> ' + a.get('a','?') + ' | ' + a.get('an','?'))
        count += 1
        if count >= 30:
            break

# Top-level keys
print('\nKeys: ' + str(list(d.keys())))
print('px2a count: ' + str(len(px2a)))
print('dx2a count: ' + str(len(d.get('dx2a',{}))))
print('adrg_mdc count: ' + str(len(d.get('adrg_mdc',{}))))
