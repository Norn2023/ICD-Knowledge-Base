"""
Split Shanghai items: old-style codes → shanghai, new-style codes → shanghai_new
Old-style: 6-9 digit codes like 110200001, 331400012, etc.
New-style: 15-digit codes starting with 01 like 013112020020000
"""
import json, gzip, re

BASE = 'D:/AI_libra/codex_Obsi/_builder/4way-mapping'

with open(f'{BASE}/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sh_all = data['shanghai']
cross_refs = data['cross_refs']

# Split by code pattern
sh_old = []  # Old Shanghai pricing codes
sh_new = []  # New unified pricing codes (from obstetrics file)
old_ids = set()
new_ids = set()

for item in sh_all:
    code = item['code']
    # New-style codes: 15 digits starting with 01
    if len(code) >= 12 and code.startswith('01'):
        sh_new.append(item)
        new_ids.add(item['id'])
    else:
        sh_old.append(item)
        old_ids.add(item['id'])

print(f'Old Shanghai: {len(sh_old)} items')
print(f'New Shanghai (obstetrics unified): {len(sh_new)} items')

# Update cross-refs: mark which ones use new-style SH codes
for ref in cross_refs:
    if ref['sh_id'] in new_ids:
        ref['_sh_source'] = 'new'  # Mark as new-style

# Re-index
sh_index = {}
pg_index = {}
ts_index = {}
icd9_index = {}
for i, ref in enumerate(cross_refs):
    if ref['sh_id']: sh_index.setdefault(ref['sh_id'], []).append(i)
    if ref['pg_id']: pg_index.setdefault(ref['pg_id'], []).append(i)
    if ref['ts_id']: ts_index.setdefault(ref['ts_id'], []).append(i)
    if ref['icd9_id']: icd9_index.setdefault(ref['icd9_id'], []).append(i)

# Update data
data['shanghai'] = sh_old
data['shanghai_new'] = sh_new
data['cross_refs'] = cross_refs
data['_index'] = {'sh': sh_index, 'pg': pg_index, 'ts': ts_index, 'icd9': icd9_index}
data['stats'] = {
    'shanghai_count': len(sh_old),
    'shanghai_new_count': len(sh_new),
    'pricing_guide_count': len(data['pricing_guide']),
    'tech_specs_count': len(data['tech_specs']),
    'icd9_count': len(data['icd9']),
    'cross_refs_count': len(cross_refs),
    'shanghai_matched': sum(1 for r in cross_refs if r['pg_id']),
    'full_chain': sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id']),
}

# Save
with open(f'{BASE}/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
with gzip.open(f'{BASE}/data.json.gz', 'wb', compresslevel=6) as f:
    f.write(json_bytes)

print(f'\nSaved ({len(json_bytes)} bytes)')
stats_str = json.dumps(data['stats'], ensure_ascii=False)
print(f'Stats: {stats_str}')
