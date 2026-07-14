"""
Fix ALL obstetric cross-refs for new SH items.
The previous rebuild_obstetric.py had a buggy new_sh_to_pg mapping.
This script:
1. Removes ALL wrong OB cross-refs (sh_code starting with 013)
2. Re-creates them with CORRECT PG mapping
3. Handles both delivery (013314) and prenatal (013112) items
"""
import json, gzip, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.dirname(BASE)

# 1. Load data
with open(os.path.join(BASE, 'data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

sh_new = data['shanghai_new']
sh_old = data['shanghai']
pg_all = data['pricing_guide']
ts_all = data['tech_specs']
icd9_all = data['icd9']
cross_refs = data['cross_refs']

# 2. Remove ALL cross-refs involving new SH OB items (codes starting with '013')
before = len(cross_refs)
cross_refs = [r for r in cross_refs if not (r.get('sh_code','') or '').startswith('013')]
removed = before - len(cross_refs)
print(f"Removed {removed} old OB cross-refs (codes starting with 013)")
print(f"Remaining: {len(cross_refs)}")

# 3. Correct PG mapping for new SH delivery items
CORRECT_NEW_SH_PG = {
    # 阴道分娩（常规）series
    'sh_4935': '阴道分娩（常规）',
    'sh_4936': '阴道分娩（常规）',
    'sh_4937': '阴道分娩（常规）',
    # 阴道分娩（复杂）series
    'sh_4938': '阴道分娩（复杂）',
    'sh_4939': '阴道分娩（复杂）',
    'sh_4940': '阴道分娩（复杂）',
    # 剖宫产（常规）series
    'sh_4942': '剖宫产（常规）',
    # 剖宫产（复杂）series
    'sh_4943': '剖宫产（复杂）',
    'sh_4944': '剖宫产（复杂）',
    # 宫颈环扎术（常规）series
    'sh_4945': '宫颈环扎术（常规）',
    'sh_4946': '宫颈环扎术（常规）',
    # 宫颈环扎术（特殊）series
    'sh_4947': '宫颈环扎术（特殊）',
    'sh_4948': '宫颈环扎术（特殊）',
    # 手术减胎
    'sh_4949': '手术减胎',
}

# 4. Read reference file for old SH → PG → TS mappings
import openpyxl
ref_file = None
for f in os.listdir(BUILDER):
    if '产科' in f and '映射' in f and f.endswith('.xlsx'):
        ref_file = os.path.join(BUILDER, f)
        break

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

wb = openpyxl.load_workbook(ref_file, read_only=True, data_only=True)
ws = wb[wb.sheetnames[0]]

map_ref = []
for row in ws.iter_rows(min_row=4, values_only=True):
    seq = str(row[0]).strip() if row[0] else ''
    pg_name = str(row[1]).strip().replace('\n','') if row[1] else ''
    sh_text = str(row[4]).strip() if len(row) > 4 and row[4] else ''
    ts_text = str(row[5]).strip() if len(row) > 5 and row[5] else ''
    if seq and pg_name:
        sh_names = [s.strip().rstrip(';') for s in sh_text.split('\n') if s.strip()] if sh_text else []
        ts_names = [s.strip() for s in ts_text.split('\n') if s.strip()] if ts_text else []
        map_ref.append({'seq': seq, 'pg_name': pg_name, 'sh_names': sh_names, 'ts_names': ts_names})
wb.close()
print(f"Reference entries: {len(map_ref)}")

# 5. Build lookups
pg_by_name = {}
for p in pg_all:
    pg_by_name[clean(p['name'])] = p

ts_by_name = {}
ts_by_code = {}
for t in ts_all:
    ts_by_code[t['code']] = t
    ts_by_name[clean(t['name'])] = t

# Load TS source for fuzzy matching
ts_source = {t['code']: t for t in ts_all}
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
    except Exception as e:
        print(f"TS source load skipped: {e}")

# 6. ICD-9 map
ob_icd9_map = {
    '阴道分娩（常规）': ('73.5900x001', '会阴切开缝合术/顺产接生'),
    '阴道分娩（复杂）': ('73.5900x002', '臀位/产钳/胎吸助产'),
    '剖宫产（常规）': ('74.1x00', '剖宫产术'),
    '剖宫产（复杂）': ('74.4x00', '剖宫产术(复杂)'),
    '宫颈环扎术（常规）': ('67.5100x001', '子宫颈环扎术'),
    '宫颈环扎术（特殊）': ('67.5900x001', '子宫颈环扎术(特殊)'),
    '手术减胎': ('73.8x01', '减胎术'),
}

icd9_id_by_code = {}
for icd in icd9_all:
    for k in ['yb_code', 'gl_code']:
        if icd.get(k):
            icd9_id_by_code[icd[k]] = icd['id']

def find_icd9(pg_name):
    for kw, (code, name) in ob_icd9_map.items():
        if kw in pg_name:
            return code, name
    return '', ''

def find_ts_items(ts_names_list):
    result = []
    for ts_name in ts_names_list:
        cname = clean(ts_name)
        if cname in ts_by_name:
            result.append(ts_by_name[cname])
            continue
        # Fuzzy in ts_source
        best_code = None
        best_score = 0
        for code, item in ts_source.items():
            score = SequenceMatcher(None, cname, clean(item['name'])).ratio()
            if score > best_score and score > 0.65:
                best_score = score
                best_code = code
        if best_code and best_code in ts_by_code:
            result.append(ts_by_code[best_code])
    return result

def add_ref(sid, sname, scode, pg, ts_item, icd9_code, icd9_name):
    ref = {
        'sh_id': sid, 'sh_name': sname, 'sh_code': scode,
        'pg_id': pg['id'], 'pg_name': pg['name'], 'pg_seq': pg['seq'], 'pg_category': pg.get('category', '产科类'),
        'ts_id': ts_item['id'] if ts_item else '',
        'ts_name': ts_item['name'] if ts_item else '',
        'ts_code': ts_item['code'] if ts_item else '',
        'icd9_id': icd9_id_by_code.get(icd9_code, ''),
        'icd9_name': icd9_name, 'icd9_code': icd9_code,
        'sh_pg_score': '0.95', 'pg_ts_score': '1.00' if ts_item else '',
    }
    cross_refs.append(ref)

# 7. Rebuild cross-refs for delivery items
new_refs = 0

for sid, pg_name in CORRECT_NEW_SH_PG.items():
    sname = next((s['name'] for s in sh_new if s['id'] == sid), '')
    scode = next((s['code'] for s in sh_new if s['id'] == sid), '')
    if not sname:
        print(f"  [SKIP] {sid} not found in shanghai_new")
        continue

    pg = pg_by_name.get(clean(pg_name))
    if not pg:
        print(f"  [SKIP] PG [{pg_name}] not found")
        continue

    # Find TS items from reference (normalize parens!)
    ts_items = []
    for mr in map_ref:
        if clean(mr['pg_name']) == clean(pg_name):
            ts_items = find_ts_items(mr['ts_names'])
            break

    icd9_code, icd9_name = find_icd9(pg_name)

    if ts_items:
        for ts in ts_items:
            add_ref(sid, sname, scode, pg, ts, icd9_code, icd9_name)
            new_refs += 1
    else:
        add_ref(sid, sname, scode, pg, None, icd9_code, icd9_name)
        new_refs += 1

    print(f"  ✓ {sid} [{sname[:35]}] → PG=[{pg_name}] ({len(ts_items)} TS, ICD9={icd9_code})")

print(f"\nDelivery refs created: {new_refs}")

# 8. Rebuild cross-refs for prenatal items (from add_prenatal_refs.py)
ob_icd9_map_prenatal = {
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

prenatal_ids = [s['id'] for s in sh_new if s['code'].startswith('013112')]
prenatal_refs = 0

for sid in prenatal_ids:
    sname = next((s['name'] for s in sh_new if s['id'] == sid), '')
    scode = next((s['code'] for s in sh_new if s['id'] == sid), '')
    if not sname:
        continue

    # Find matching PG from reference
    best_mr = None
    best_score = 0
    for mr in map_ref:
        score = SequenceMatcher(None, clean(sname), clean(mr['pg_name'])).ratio()
        if score > best_score:
            best_score = score
            best_mr = mr

    if not best_mr or best_score < 0.4:
        continue

    pg_name = best_mr['pg_name']
    pg = pg_by_name.get(clean(pg_name))
    if not pg:
        continue

    ts_items = find_ts_items(best_mr['ts_names'])
    icd9_code, icd9_name = '', ''
    for kw, (code, name) in ob_icd9_map_prenatal.items():
        if kw in pg_name:
            icd9_code, icd9_name = code, name
            break

    if ts_items:
        for ts in ts_items:
            add_ref(sid, sname, scode, pg, ts, icd9_code, icd9_name)
            prenatal_refs += 1
    else:
        add_ref(sid, sname, scode, pg, None, icd9_code, icd9_name)
        prenatal_refs += 1

print(f"Prenatal refs created: {prenatal_refs}")

# 9. Also rebuild old SH → PG cross-refs
old_ob_refs = 0
for mr in map_ref:
    pg_name = mr['pg_name']
    pg = pg_by_name.get(clean(pg_name))
    if not pg:
        continue

    for sh_name in mr['sh_names']:
        idx, score = fuzzy_match(sh_name, sh_old, 'name', threshold=0.5)
        if idx < 0:
            continue
        sh = sh_old[idx]
        ts_items = find_ts_items(mr['ts_names'])
        icd9_code, icd9_name = find_icd9(pg_name)
        # Also check prenatal map
        if not icd9_code:
            for kw, (code, name) in ob_icd9_map_prenatal.items():
                if kw in pg_name:
                    icd9_code, icd9_name = code, name
                    break

        if ts_items:
            for ts in ts_items:
                add_ref(sh['id'], sh['name'], sh['code'], pg, ts, icd9_code, icd9_name)
                old_ob_refs += 1
        else:
            add_ref(sh['id'], sh['name'], sh['code'], pg, None, icd9_code, icd9_name)
            old_ob_refs += 1

print(f"Old SH → PG refs created: {old_ob_refs}")
print(f"Total new refs: {new_refs + prenatal_refs + old_ob_refs}")

# 10. Rebuild index
sh_idx = {}; pg_idx = {}; ts_idx = {}; icd9_idx = {}
for i, ref in enumerate(cross_refs):
    if ref['sh_id']: sh_idx.setdefault(ref['sh_id'], []).append(i)
    if ref['pg_id']: pg_idx.setdefault(ref['pg_id'], []).append(i)
    if ref['ts_id']: ts_idx.setdefault(ref['ts_id'], []).append(i)
    if ref['icd9_id']: icd9_idx.setdefault(ref['icd9_id'], []).append(i)

data['cross_refs'] = cross_refs
data['_index'] = {'sh': sh_idx, 'pg': pg_idx, 'ts': ts_idx, 'icd9': icd9_idx}

# Update stats
dc = data.setdefault('stats', {})
dc['cross_refs_count'] = len(cross_refs)
dc['shanghai_count'] = len(sh_old)
dc['shanghai_new_count'] = len(sh_new)
dc['pricing_guide_count'] = len(pg_all)
dc['tech_specs_count'] = len(ts_all)
dc['icd9_count'] = len(icd9_all)
dc['shanghai_matched'] = sum(1 for r in cross_refs if r['pg_id'])
dc['full_chain'] = sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id'])

# 11. Save
with open(os.path.join(BASE, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
with gzip.open(os.path.join(BASE, 'data.json.gz'), 'wb', compresslevel=6) as f:
    f.write(jbytes)

print(f"\n{'='*50}")
print(f"RESULTS:")
print(f"  Cross-refs: {len(cross_refs)} (removed {removed}, added {new_refs + prenatal_refs + old_ob_refs})")
print(f"  Full chain: {dc['full_chain']}")
print(f"  File size: {len(jbytes):,} bytes")
print(f"Done!")
