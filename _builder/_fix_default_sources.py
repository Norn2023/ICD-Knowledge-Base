"""Fix missing source badges"""
import gzip, json

with gzip.open('4way-mapping/data.json.gz','rb') as f:
    data = json.loads(f.read())

cross_refs = data['cross_refs']
pg_items = data['pricing_guide']

# For items without source, default to project_name
fixed = 0
for ref in cross_refs:
    if ref.get('ts_name') and not ref.get('ts_source'):
        ref['ts_source'] = 'project_name'
        fixed += 1
    if ref.get('sh_name') and not ref.get('sh_source'):
        ref['sh_source'] = 'project_name'
        fixed += 1

print(f'Default-source fixed: {fixed}')

# Check 会阴裂伤 items specifically
print('\n=== 会阴裂伤 items ===')
for ref in cross_refs:
    tsn = ref.get('ts_name', '')
    if '会阴' in tsn and '裂伤' in tsn:
        print(f'  ts={tsn} source={ref.get("ts_source")} icd9={ref.get("icd9_code")}')

# Save
with gzip.open('4way-mapping/data.json.gz','wb', compresslevel=6) as f:
    f.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
print('\nSaved OK')
