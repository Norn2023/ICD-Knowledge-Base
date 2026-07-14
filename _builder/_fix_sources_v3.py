"""Mark source badges - heuristic: 加收/扩展 items' TS → into_price"""
import gzip, json

with gzip.open('4way-mapping/data.json.gz','rb') as f:
    data = json.loads(f.read())

cross_refs = data['cross_refs']
sh_new = data['shanghai_new']

# Build set of 加收/扩展 SH item IDs
surcharge_ids = set()
for s in sh_new:
    name = s.get('name', '')
    if '加收' in name or '扩展' in name:
        surcharge_ids.add(s['id'])

print(f'加收/扩展 items: {len(surcharge_ids)}')

# Apply source badges
# Rule: if item is 加收/扩展 variant → TS source = into_price, SH source = project_name
# Otherwise → both sources = project_name
for ref in cross_refs:
    sid = ref.get('sh_id', '')
    if sid in surcharge_ids:
        # 加收/扩展: TS is 纳入价格构成
        ref['ts_source'] = 'into_price'
        ref['sh_source'] = 'project_name'
    else:
        # Normal item: both are 项目名称
        if not ref.get('ts_source'):
            ref['ts_source'] = 'project_name'
        if not ref.get('sh_source'):
            ref['sh_source'] = 'project_name'

# Count
sources = {}
for ref in cross_refs:
    ts = ref.get('ts_source', 'none')
    sh = ref.get('sh_source', 'none')
    sources[f'ts={ts}'] = sources.get(f'ts={ts}', 0) + 1
    sources[f'sh={sh}'] = sources.get(f'sh={sh}', 0) + 1
print(f'Source counts: {sources}')

# Save
with gzip.open('4way-mapping/data.json.gz', 'wb', compresslevel=6) as f:
    f.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
print('Saved OK')
