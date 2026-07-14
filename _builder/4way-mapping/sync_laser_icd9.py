"""Sync ICD-9 code 93.3900x001 物理疗法 to all laser therapy items."""
import json, gzip

BASE = 'D:/AI_libra/codex_Obsi/_builder/4way-mapping'

with open(f'{BASE}/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cross_refs = data['cross_refs']
icd9_items = data['icd9']

# Add ICD-9 item if not exists
laser_icd9_id = None
for item in icd9_items:
    if item.get('yb_code') == '93.3900x001':
        laser_icd9_id = item['id']
        break

if not laser_icd9_id:
    laser_icd9_id = f'icd9_{len(icd9_items)}'
    icd9_items.append({
        'id': laser_icd9_id,
        'yb_code': '93.3900x001',
        'yb_name': '物理疗法',
        'gl_code': '93.3900x001',
        'gl_name': '物理疗法',
    })
    print(f'Added ICD-9 item: {laser_icd9_id}')
else:
    print(f'ICD-9 item exists: {laser_icd9_id}')

# Find all laser therapy cross-refs
# Laser items identified by: 激光 in SH name, PG name, or specific codes
laser_codes = [
    '430000019',  # 激光针
    '340100005',  # 激光疗法
    '330804066',  # 激光血管...
    '330804067',
    '330401013',
    '310300057',
    '310300079',
    '310300081',
    '310300083',
    '310300084',
    '320500004',
    '320100002',
    '311400036',  # 氦氖激光
    '310401049c',
    '310402025c',
    '310403016c',
]

updated = 0
for ref in cross_refs:
    if ref.get('sh_code') in laser_codes or '激光' in (ref.get('sh_name', '') + ref.get('pg_name', '')):
        ref['icd9_id'] = laser_icd9_id
        ref['icd9_code'] = '93.3900x001'
        ref['icd9_name'] = '物理疗法'
        updated += 1

print(f'Updated {updated} cross-refs with ICD-9 93.3900x001')

# Also search Shanghai items for laser and ensure all SH items with 激光 are linked
laser_sh_ids = set()
for s in data['shanghai']:
    if '激光' in (s.get('name', '') + s.get('desc', '')):
        laser_sh_ids.add(s['id'])

# For each laser SH item without a cross-ref, create one linked to laser_icd9
for sh_id in laser_sh_ids:
    exists = any(ref['sh_id'] == sh_id for ref in cross_refs)
    if not exists:
        # Find the SH item
        sh = next((s for s in data['shanghai'] if s['id'] == sh_id), None)
        if sh:
            cross_refs.append({
                'sh_id': sh_id,
                'sh_name': sh['name'],
                'sh_code': sh['code'],
                'pg_id': '',
                'pg_name': '',
                'pg_seq': '',
                'pg_category': '',
                'ts_id': '',
                'ts_name': '',
                'ts_code': '',
                'icd9_id': laser_icd9_id,
                'icd9_code': '93.3900x001',
                'icd9_name': '物理疗法',
                'sh_pg_score': '',
                'pg_ts_score': '',
            })
            updated += 1
            print(f'  New SH link: {sh["code"]} {sh["name"]}')

# Also check shanghai_new
for s in data.get('shanghai_new', []):
    if '激光' in (s.get('name', '') + s.get('desc', '')):
        laser_sh_ids.add(s['id'])

# Rebuild index
sh_index = {}
pg_index = {}
ts_index = {}
icd9_index = {}
for i, ref in enumerate(cross_refs):
    if ref['sh_id']: sh_index.setdefault(ref['sh_id'], []).append(i)
    if ref['pg_id']: pg_index.setdefault(ref['pg_id'], []).append(i)
    if ref['ts_id']: ts_index.setdefault(ref['ts_id'], []).append(i)
    if ref['icd9_id']: icd9_index.setdefault(ref['icd9_id'], []).append(i)

data['icd9'] = icd9_items
data['cross_refs'] = cross_refs
data['_index'] = {'sh': sh_index, 'pg': pg_index, 'ts': ts_index, 'icd9': icd9_index}
data['stats']['icd9_count'] = len(icd9_items)
data['stats']['cross_refs_count'] = len(cross_refs)
data['stats']['full_chain'] = sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id'])

# Save
with open(f'{BASE}/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
with gzip.open(f'{BASE}/data.json.gz', 'wb', compresslevel=6) as f:
    f.write(json_bytes)

fc = data['stats']['full_chain']
print(f'\nTotal cross-refs: {len(cross_refs)}')
print(f'ICD-9 items: {len(icd9_items)}')
print(f'Full chain: {fc}')
print('Done')
