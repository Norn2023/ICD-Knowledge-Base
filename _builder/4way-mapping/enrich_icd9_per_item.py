"""
Enrich OB cross-refs with per-item ICD-9 codes.
Each old SH item and TS item gets its own ICD-9 code (not just PG-level).
"""
import json, gzip, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# ── Per-item ICD-9 mapping from vault data ──
# Format: name → (code, icd9_name)
# Priority: specific SH/TS name > PG level
ITEM_ICD9 = {
    # ── Old SH items (by name) ──
    '单胎顺产接生': ('73.5900x002', '头位阴道助产'),
    '双胎接生': ('73.5900x002', '头位阴道助产'),
    '多胎接生': ('73.5900x002', '头位阴道助产'),
    '脐带还纳术': ('73.5900x002', '头位阴道助产'),
    '难产接生': ('73.5900x001', '臀助产术'),
    '剖宫产术': ('74.1x00', '低位子宫下段剖宫产'),
    '子宫颈管环扎术': ('67.5100x001', '子宫颈环扎术'),
    '选择性减胎术': ('73.8x01', '选择性减胎术'),
    '死胎接生': ('73.8x00', '对胎儿手术帮助分娩'),
    '产钳助产术': ('72.4x00', '产钳胎头旋转'),
    '胎头吸引术': ('72.7900x001', '胎头吸引术'),
    '臀位牵引术': ('72.5400x001', '全部臀位牵引术'),
    '外倒转术': ('73.2100x001', '内倒转助产'),

    # ── TS items (by name) ──
    '会阴Ⅰ-Ⅱ度裂伤缝合术': ('75.6902', '近期产科会阴裂伤修补术'),
    '会阴切开缝合术': ('73.6x01', '会阴侧切缝合术'),
    '手取胎盘术': ('75.4x00x002', '手取胎盘'),
    '脐带残端处置术': ('73.5900x002', '头位阴道助产'),
    '单胎顺产接生': ('73.5900x002', '头位阴道助产'),
    '多胎接生': ('73.5900x002', '头位阴道助产'),
    '臀助产术': ('73.5900x001', '臀助产术'),
    '胎头旋转术': ('73.51', '手法旋转胎头'),
    '内倒转术': ('73.2100x001', '内倒转助产'),
    '外倒转术': ('73.91', '胎位外倒转术'),
    '古典式剖宫产术': ('74.1x00', '低位子宫下段剖宫产'),
    '子宫下段剖宫产术': ('74.1x00', '低位子宫下段剖宫产'),
    '腹膜外剖宫产术': ('74.2x00', '腹膜外剖宫产'),
    '瘢痕子宫剖宫产术': ('74.4x00', '其他特指类型的剖宫产'),
    '腹腔妊娠取胎术': ('74.4x01', '腹腔妊娠剖宫产术'),
    '胎盘植入剖宫产保留子宫术': ('74.4x00', '其他特指类型的剖宫产'),
    '分娩时人工破膜': ('73.0900x001', '分娩时人工破膜'),
    '低位人工破膜术': ('73.0900x001', '分娩时人工破膜'),
    '高位人工破膜术': ('73.0900x001', '分娩时人工破膜'),
    '胎头吸引助产术': ('72.7900x001', '胎头吸引术'),
    '产钳助产术': ('72.4x00', '产钳胎头旋转'),
    '臀位牵引术': ('72.5400x001', '全部臀位牵引术'),
    '臀位助产术': ('73.5900x001', '臀助产术'),
    '胎儿锁骨切断助产术': ('73.8x00x006', '胎儿锁骨切断助产术'),
    '经阴道宫颈内口环扎术(MacDonald手术)': ('67.5900x001', '子宫颈环扎术[Shirodkar]'),
    '经阴道子宫颈环扎术': ('67.5901', '经阴道子宫颈环扎术'),
    '妊娠期紧急宫颈环扎术': ('67.5900x001', '子宫颈环扎术[Shirodkar]'),
    '超声引导下脐带电凝术': ('73.8x01', '选择性减胎术'),
    '经胎儿镜脐带电凝术': ('73.8x01', '选择性减胎术'),
    '经胎儿镜胎儿脐带结扎术': ('73.8x01', '选择性减胎术'),
    '死胎接生': ('73.8x00', '对胎儿手术帮助分娩'),
    '死胎分解术': ('73.8x02', '碎胎术'),
}

# Build icd9 ID lookup
icd9_by_code = {}
for icd in data['icd9']:
    if icd.get('yb_code'): icd9_by_code[icd['yb_code']] = icd['id']
    if icd.get('gl_code'): icd9_by_code[icd['gl_code']] = icd['id']

# ── Update cross-refs with per-item ICD-9 ──
updated = 0
for c in data['cross_refs']:
    # Only update OB-related cross-refs (those with OB pg_category)
    if c.get('pg_category') != '产科类':
        continue

    sh_name = c.get('sh_name', '')
    ts_name = c.get('ts_name', '')
    current_icd9 = c.get('icd9_code', '')

    # Try TS name first (most specific)
    best_code = ''
    best_name = ''
    for name_key, (code, icd_name) in ITEM_ICD9.items():
        if ts_name and name_key in ts_name:
            best_code = code
            best_name = icd_name
            break

    # Then try SH name
    if not best_code:
        for name_key, (code, icd_name) in ITEM_ICD9.items():
            if sh_name and name_key in sh_name:
                best_code = code
                best_name = icd_name
                break

    if best_code and best_code != current_icd9:
        c['icd9_code'] = best_code
        c['icd9_name'] = best_name
        c['icd9_id'] = icd9_by_code.get(best_code, c.get('icd9_id', ''))
        updated += 1

print(f"Updated {updated} cross-refs with per-item ICD-9 codes")

# ── Ensure missing ICD-9 items exist ──
missing = set()
for c in data['cross_refs']:
    code = c.get('icd9_code', '')
    if code and code not in icd9_by_code:
        missing.add(code)

print(f"Missing ICD-9 items in table: {len(missing)}")
for code in sorted(missing):
    name = ''
    for _, (c, n) in ITEM_ICD9.items():
        if c == code:
            name = n
            break
    if not name:
        name = code
    # Add to icd9 table
    next_id = f'icd9_{len(data["icd9"])}'
    data['icd9'].append({
        'id': next_id,
        'yb_code': code,
        'yb_name': name,
        'gl_code': code,
        'gl_name': name,
    })
    icd9_by_code[code] = next_id
    print(f"  + Added: {next_id} [{code}] {name}")

# Update icd9_id for cross-refs where code exists but id was missing
fixed_ids = 0
for c in data['cross_refs']:
    code = c.get('icd9_code', '')
    if code and not c.get('icd9_id'):
        if code in icd9_by_code:
            c['icd9_id'] = icd9_by_code[code]
            fixed_ids += 1

print(f"Fixed {fixed_ids} cross-refs with icd9_ids")

# ── Rebuild index ──
sh_idx = {}; pg_idx = {}; ts_idx = {}; icd9_idx = {}
for i, ref in enumerate(data['cross_refs']):
    if ref['sh_id']: sh_idx.setdefault(ref['sh_id'], []).append(i)
    if ref['pg_id']: pg_idx.setdefault(ref['pg_id'], []).append(i)
    if ref['ts_id']: ts_idx.setdefault(ref['ts_id'], []).append(i)
    if ref['icd9_id']: icd9_idx.setdefault(ref['icd9_id'], []).append(i)

data['_index'] = {'sh': sh_idx, 'pg': pg_idx, 'ts': ts_idx, 'icd9': icd9_idx}
dc = data.setdefault('stats', {})
dc['icd9_count'] = len(data['icd9'])
dc['cross_refs_count'] = len(data['cross_refs'])
dc['full_chain'] = sum(1 for r in data['cross_refs'] if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id'])

# ── Save ──
with open(os.path.join(BASE, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
import gzip as gz
with gz.open(os.path.join(BASE, 'data.json.gz'), 'wb', compresslevel=6) as f:
    f.write(jbytes)

# ── Summary ──
print(f"\n{'='*50}")
print(f"ICD-9 items: {len(data['icd9'])}")
print(f"Cross-refs: {len(data['cross_refs'])}")
print(f"Full chain: {dc['full_chain']}")

# Sample per-item ICD-9 distribution for 阴道分娩常规
print(f"\n=== Sample: ICD-9 codes for 阴道分娩常规 cross-refs ===")
from collections import Counter
icd9_dist = Counter()
for c in data['cross_refs']:
    if c.get('pg_name') == '阴道分娩（常规）':
        icd9_dist[c.get('icd9_code', 'NONE')] += 1
for code, count in icd9_dist.most_common():
    print(f"  {code}: {count} refs")
