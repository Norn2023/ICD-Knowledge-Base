"""
Add missing cross-refs for 产前检查/操作类 new SH items (sh_4914-sh_4934).
Reads the obstetric mapping reference to match new SH → PG → old SH → TS → ICD9.
"""
import json, gzip, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.dirname(BASE)

# 1. Load current data
with open(os.path.join(BASE, 'data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

sh_new = data['shanghai_new']
sh_old = data['shanghai']
pg_all = data['pricing_guide']
ts_all = data['tech_specs']
icd9_all = data['icd9']
cross_refs = data['cross_refs']

# 2. Read reference mapping file
import openpyxl
ref_file = None
for f in os.listdir(BUILDER):
    if '产科' in f and '映射' in f and f.endswith('.xlsx'):
        ref_file = os.path.join(BUILDER, f)
        break

if not ref_file:
    print("ERROR: Reference file not found")
    sys.exit(1)

wb = openpyxl.load_workbook(ref_file, read_only=True, data_only=True)
ws = wb[wb.sheetnames[0]]

# Read mapping reference: seq -> (pg_name, old_sh_names, ts_names)
map_ref = []
for row in ws.iter_rows(min_row=4, values_only=True):
    seq = str(row[0]).strip() if row[0] else ''
    pg_name = str(row[1]).strip().replace('\n','') if row[1] else ''
    sh_text = str(row[4]).strip() if len(row) > 4 and row[4] else ''
    ts_text = str(row[5]).strip() if len(row) > 5 and row[5] else ''
    if seq and pg_name:
        sh_names = [s.strip().rstrip(';') for s in sh_text.split('\n') if s.strip()] if sh_text else []
        ts_names = [s.strip() for s in ts_text.split('\n') if s.strip()] if ts_text else []
        map_ref.append({
            'seq': seq, 'pg_name': pg_name,
            'sh_names': sh_names, 'ts_names': ts_names,
        })
wb.close()
print(f"Reference entries loaded: {len(map_ref)}")
for mr in map_ref:
    print(f"  seq={mr['seq']:>3} pg=[{mr['pg_name']}] sh={mr['sh_names'][:2]} ts={mr['ts_names'][:2]}")

# 3. Build lookup dictionaries
from difflib import SequenceMatcher

def clean(s):
    return s.replace('\n','').replace(' ','').replace('（','(').replace('）',')').replace(';','').replace(':','').strip()

def fuzzy_match(target, candidates, key='name', threshold=0.55):
    ct = clean(target)
    best_score, best_idx = 0, -1
    for i, c in enumerate(candidates):
        cn = clean(c.get(key, ''))
        if not cn: continue
        if ct == cn: return i, 1.0
        if ct in cn or cn in ct: return i, 0.95
        score = SequenceMatcher(None, ct, cn).ratio()
        if score > best_score: best_score, best_idx = score, i
    return (best_idx, best_score) if best_score >= threshold else (-1, 0)

pg_by_name = {}
for p in pg_all:
    pg_by_name[clean(p['name'])] = p

ts_by_name = {}
ts_by_code = {}
for t in ts_all:
    ts_by_code[t['code']] = t
    ts_by_name[clean(t['name'])] = t

# 4. Ensure all PG items exist (add missing ones)
new_pg_added = 0
for mr in map_ref:
    cname = clean(mr['pg_name'])
    if cname not in pg_by_name:
        new_pg = {
            'id': f'pg_{len(pg_all)}',
            'seq': mr['seq'],
            'category': '产科类',
            'name': mr['pg_name'],
            'output': '',
            'cost_structure': '',
            'unit': '次',
        }
        pg_all.append(new_pg)
        pg_by_name[cname] = new_pg
        new_pg_added += 1
        print(f"  + Added PG: {mr['pg_name']} (pg_{len(pg_all)-1})")
print(f"New PG items added: {new_pg_added}")

# 5. ICD-9 codes for OB procedures
ob_icd9_map = {
    '产前常规检查': ('75.3x00', '产前常规检查'),
    '胎心监测': ('75.3400x001', '胎心监测'),
    '催引产': ('73.4x00', '药物引产'),
    '产程管理': ('73.5900x003', '产程观察'),
    '分娩镇痛': ('03.9100x001', '椎管内麻醉分娩镇痛'),
    '导乐分娩': ('73.5900x004', '导乐分娩'),
    '亲情陪产': ('73.5900x005', '亲情陪产'),
    '胎儿外倒转': ('73.2100x001', '外倒转术'),
    '胎儿宫内输血': ('75.3500x001', '胎儿宫内输血'),
    '胎盘血管交通支凝固治疗': ('75.3600x001', '胎儿血管激光凝固术'),
    '羊水调节': ('75.3700x001', '羊水调节'),
    '子宫压迫止血': ('75.9900x001', '子宫压迫止血'),
    '羊膜腔穿刺': ('75.1x00', '羊膜腔穿刺术'),
    '脐静脉穿刺': ('38.9100x001', '脐静脉穿刺术'),
    '绒毛取材': ('75.1x02', '绒毛取材'),
    '胎儿内镜检查': ('75.1x01', '胎儿镜检查'),
    '药物减胎': ('73.8x01', '减胎术'),
    '中期引产': ('73.4x00', '中期引产'),
    '晚期引产': ('73.4x01', '晚期引产'),
    '死胎接生': ('73.8x00', '死胎接生/碎胎术'),
}
# Also match by partial name
def find_icd9(pg_name):
    for kw, (code, name) in ob_icd9_map.items():
        if kw in pg_name or pg_name in kw:
            return code, name
    return '', ''

# 6. Map new SH items to PG names
# Build mapping: new SH item ID -> PG name from reference
# Match by checking if new SH name appears in or near PG name
new_sh_pg_map = {}

for s in sh_new:
    sid = s['id']
    sname = s['name']
    # Skip already mapped items
    already_mapped = any(c.get('sh_id') == sid for c in cross_refs)
    if already_mapped:
        continue

    # Find matching PG from reference
    best_mr = None
    best_score = 0
    for mr in map_ref:
        # Check if new SH name matches PG name or vice versa
        score = SequenceMatcher(None, clean(sname), clean(mr['pg_name'])).ratio()
        if score > best_score:
            best_score = score
            best_mr = mr

    if best_mr and best_score >= 0.4:
        new_sh_pg_map[sid] = best_mr['pg_name']
        print(f"  Map: {sid} [{sname[:45]}] → PG [{best_mr['pg_name'][:45]}] (score={best_score:.2f})")
    else:
        print(f"  NO MATCH: {sid} [{sname[:45]}] (best_score={best_score:.2f})")

print(f"\nNew SH→PG mappings: {len(new_sh_pg_map)}")

# 7. Build cross-refs
def add_cross_ref(sid, sname, scode, pg, ts_item, icd9_code, icd9_name):
    ref = {
        'sh_id': sid, 'sh_name': sname, 'sh_code': scode,
        'pg_id': pg['id'], 'pg_name': pg['name'], 'pg_seq': pg['seq'], 'pg_category': pg['category'],
        'ts_id': ts_item['id'] if ts_item else '',
        'ts_name': ts_item['name'] if ts_item else '',
        'ts_code': ts_item['code'] if ts_item else '',
        'icd9_id': '', 'icd9_name': icd9_name, 'icd9_code': icd9_code,
        'sh_pg_score': '0.95', 'pg_ts_score': '1.00' if ts_item else '',
    }
    # Add ICD-9 ID if we have a matching ICD-9 item
    if icd9_code:
        for icd in icd9_all:
            if icd.get('yb_code') == icd9_code or icd.get('gl_code') == icd9_code:
                ref['icd9_id'] = icd['id']
                break
    cross_refs.append(ref)

# For each mapping reference entry, find TS items
# Use existing TS data + openpyxl for missing items
ts_source = {}
for t in ts_all:
    ts_source[t['code']] = t

# Also try to load TS from Excel source if needed (using openpyxl, not pandas)
ts_xlsx = os.path.join(BUILDER, '全国医疗服务项目技术规范--2023全.xlsx')
if os.path.exists(ts_xlsx):
    try:
        wb2 = openpyxl.load_workbook(ts_xlsx, read_only=True, data_only=True)
        for sname in ['K', 'H']:
            if sname in wb2.sheetnames:
                ws2 = wb2[sname]
                for row in ws2.iter_rows(min_row=2, values_only=True):
                    if not row or not row[0]: continue
                    code = str(row[0]).strip() if row[0] else ''
                    if not code or len(code) < 6: continue
                    if code not in ts_source:
                        name_cn = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                        desc = str(row[4]).strip() if len(row) > 4 and row[4] else ''
                        if name_cn:
                            ts_source[code] = {'code': code, 'name': name_cn, 'desc': desc[:300]}
        wb2.close()
        print(f"TS source lookup: {len(ts_source)} items")
    except Exception as e:
        print(f"TS Excel load skipped: {e}")
else:
    print(f"TS source lookup: {len(ts_source)} items (existing only)")

new_refs = 0

for sid, pg_name in new_sh_pg_map.items():
    sname = next(s['name'] for s in sh_new if s['id'] == sid)
    scode = next(s['code'] for s in sh_new if s['id'] == sid)

    # Find PG item
    pg = pg_by_name.get(clean(pg_name))
    if not pg:
        print(f"  [SKIP] PG not found: {pg_name}")
        continue

    # Find TS items for this PG from reference
    ts_items = []
    for mr in map_ref:
        if mr['pg_name'] == pg_name:
            for ts_name in mr['ts_names']:
                cname = clean(ts_name)
                if cname in ts_by_name:
                    ts_items.append(ts_by_name[cname])
                else:
                    # Try fuzzy in ts_source
                    best_score = 0
                    best_code = None
                    for code, item in ts_source.items():
                        score = SequenceMatcher(None, cname, clean(item['name'])).ratio()
                        if score > best_score and score > 0.65:
                            best_score = score
                            best_code = code
                    if best_code and best_code in ts_by_code:
                        ts_items.append(ts_by_code[best_code])
            break

    # ICD-9
    icd9_code, icd9_name = find_icd9(pg_name)

    # Create cross-refs
    if ts_items:
        for ts in ts_items:
            add_cross_ref(sid, sname, scode, pg, ts, icd9_code, icd9_name)
            new_refs += 1
    else:
        add_cross_ref(sid, sname, scode, pg, None, icd9_code, icd9_name)
        new_refs += 1

    print(f"  + {sid} ({sname[:30]}): {len(ts_items)} TS, ICD9=[{icd9_code}]")

print(f"\nNew cross-refs created: {new_refs}")

# 8. Also create old SH → PG cross-refs (for reference PG mapping)
# For each PG in the reference, link old SH items
old_refs = 0
for mr in map_ref:
    pg_name = mr['pg_name']
    pg = pg_by_name.get(clean(pg_name))
    if not pg:
        continue

    # Check if old SH items for this PG already have cross-refs
    for sh_name in mr['sh_names']:
        idx, score = fuzzy_match(sh_name, sh_old, 'name', threshold=0.5)
        if idx < 0:
            continue
        sh = sh_old[idx]

        # Check if this cross-ref already exists
        exists = any(
            c.get('sh_id') == sh['id'] and c.get('pg_id') == pg['id']
            for c in cross_refs
        )
        if exists:
            continue

        # Find TS items for this PG
        ts_items = []
        for ts_name in mr['ts_names']:
            cname = clean(ts_name)
            if cname in ts_by_name:
                ts_items.append(ts_by_name[cname])
            else:
                best_score = 0
                best_code = None
                for code, item in ts_source.items():
                    score = SequenceMatcher(None, cname, clean(item['name'])).ratio()
                    if score > best_score and score > 0.65:
                        best_score = score
                        best_code = code
                if best_code and best_code in ts_by_code:
                    ts_items.append(ts_by_code[best_code])

        icd9_code, icd9_name = find_icd9(pg_name)

        if ts_items:
            for ts in ts_items:
                add_cross_ref(sh['id'], sh['name'], sh['code'], pg, ts, icd9_code, icd9_name)
                old_refs += 1
        else:
            add_cross_ref(sh['id'], sh['name'], sh['code'], pg, None, icd9_code, icd9_name)
            old_refs += 1

print(f"Old SH → PG cross-refs added: {old_refs}")

# 9. Rebuild index
sh_idx = {}; pg_idx = {}; ts_idx = {}; icd9_idx = {}
for i, ref in enumerate(cross_refs):
    if ref['sh_id']: sh_idx.setdefault(ref['sh_id'], []).append(i)
    if ref['pg_id']: pg_idx.setdefault(ref['pg_id'], []).append(i)
    if ref['ts_id']: ts_idx.setdefault(ref['ts_id'], []).append(i)
    if ref['icd9_id']: icd9_idx.setdefault(ref['icd9_id'], []).append(i)

data['shanghai'] = sh_old
data['shanghai_new'] = sh_new
data['pricing_guide'] = pg_all
data['tech_specs'] = ts_all
data['icd9'] = icd9_all
data['cross_refs'] = cross_refs
data['_index'] = {'sh': sh_idx, 'pg': pg_idx, 'ts': ts_idx, 'icd9': icd9_idx}

dc = data['stats']
dc['shanghai_count'] = len(sh_old)
dc['shanghai_new_count'] = len(sh_new)
dc['pricing_guide_count'] = len(pg_all)
dc['tech_specs_count'] = len(ts_all)
dc['icd9_count'] = len(icd9_all)
dc['cross_refs_count'] = len(cross_refs)
dc['shanghai_matched'] = sum(1 for r in cross_refs if r['pg_id'])
dc['full_chain'] = sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id'])

# 10. Save
with open(os.path.join(BASE, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
import gzip as gz
with gz.open(os.path.join(BASE, 'data.json.gz'), 'wb', compresslevel=6) as f:
    f.write(jbytes)

print(f"\n{'='*50}")
print(f"RESULTS:")
print(f"  PG items: {len(pg_all)} (+{new_pg_added})")
print(f"  Cross-refs: {len(cross_refs)} (+{new_refs + old_refs})")
print(f"  Full chain (SH+PG+TS+ICD9): {dc['full_chain']}")
print(f"  File size: {len(jbytes):,} bytes")
print(f"Done!")
