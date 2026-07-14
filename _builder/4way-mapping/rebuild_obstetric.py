"""
Complete rebuild of obstetric 4-way mappings based on:
上海市产科类医疗服务价格项目立项指南映射关系（参考）.xlsx
"""
import json, gzip, os, sys, io, pandas as pd
from difflib import SequenceMatcher

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.dirname(BASE)

def clean(s):
    return s.replace('\n','').replace(' ','').replace('（','(').replace('）',')').replace(';','').replace(':','').strip()

def fuzzy_match(target, candidates, key='name', threshold=0.6):
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

def main():
    print("=== 1. Loading data files ===")

    # Load current mapping data
    with open(f'{BASE}/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    sh_all = data['shanghai']
    sh_new = data.get('shanghai_new', [])
    pg_all = data['pricing_guide']
    ts_all = data['tech_specs']
    icd9_all = data['icd9']
    cross_refs = data['cross_refs']

    # Load full TS data from source to find missing items
    xls = pd.ExcelFile(f'{BUILDER}/全国医疗服务项目技术规范--2023全.xlsx')
    ts_lookup = {}
    for sheet_idx in [6, 7]:  # K and H sheets
        df = pd.read_excel(xls, sheet_name=sheet_idx)
        for idx, row in df.iterrows():
            code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            if not code or len(code) < 6: continue
            name_cn = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
            desc = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
            if name_cn:
                ts_lookup[code] = {'code': code, 'name': name_cn, 'desc': desc[:300]}
    print(f'TS source items (K+H sheets): {len(ts_lookup)}')

    # Load mapping reference
    map_file = f'{BUILDER}/上海市产科类医疗服务价格项目立项指南映射关系（参考）.xlsx'
    import openpyxl
    wb = openpyxl.load_workbook(map_file, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]

    map_ref = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        seq = str(row[0]).strip() if row[0] else ''
        pg_name = str(row[1]).strip().replace('\n','') if row[1] else ''
        sh_text = str(row[4]).strip() if row[4] else ''
        ts_text = str(row[5]).strip() if row[5] else ''

        if seq and pg_name:
            sh_names = [s.strip().rstrip(';') for s in sh_text.split('\n') if s.strip()]
            ts_names = [s.strip() for s in ts_text.split('\n') if s.strip()]
            map_ref.append({
                'seq': seq, 'pg_name': pg_name,
                'sh_names': sh_names, 'ts_names': ts_names,
            })
    wb.close()
    print(f'Mapping reference items: {len(map_ref)}')

    # ICD-9 codes for common OB procedures
    ob_icd9_map = {
        '阴道分娩（常规）': ('73.5900x001', '会阴切开缝合术/顺产接生'),
        '阴道分娩（复杂）': ('73.5900x002', '臀位/产钳/胎吸助产'),
        '剖宫产（常规）': ('74.1x00', '剖宫产术'),
        '剖宫产（复杂）': ('74.4x00', '剖宫产术(复杂)'),
        '宫颈环扎术（常规）': ('67.5100x001', '子宫颈环扎术'),
        '宫颈环扎术（特殊）': ('67.5900x001', '子宫颈环扎术(特殊)'),
        '分娩镇痛': ('03.9100x001', '椎管内麻醉分娩镇痛'),
        '死胎接生': ('73.8x00', '死胎接生/碎胎术'),
        '胎儿外倒转': ('73.2100x001', '外倒转术'),
        '催引产': ('73.4x00', '药物引产'),
        '羊膜腔穿刺': ('75.1x00', '羊膜腔穿刺术'),
        '胎儿内镜检查': ('75.1x01', '胎儿镜检查'),
        '减胎术': ('73.8x01', '减胎术'),
        '子宫压迫止血': ('75.9900x001', '子宫压迫止血'),
        '产前常规检查': ('75.3x00', '产前常规检查'),
        '胎心监测': ('75.3400x001', '胎心监测'),
        '脐静脉穿刺': ('38.9100x001', '脐静脉穿刺术'),
        '绒毛取材': ('75.1x02', '绒毛取材'),
        '羊水调节': ('75.3900x001', '羊水调节'),
    }

    print("\n=== 2. Adding missing PG items ===")
    existing_pg_names = set(clean(p['name']) for p in pg_all)
    new_pg_added = 0

    for mr in map_ref:
        pg_name = mr['pg_name']
        cname = clean(pg_name)
        if cname not in existing_pg_names:
            new_pg = {
                'id': f'pg_{len(pg_all)}',
                'seq': mr['seq'],
                'category': '产科类',
                'name': pg_name,
                'output': '',
                'cost_structure': '',
                'unit': '次',
            }
            pg_all.append(new_pg)
            existing_pg_names.add(cname)
            new_pg_added += 1
            print(f'  Added PG: {pg_name}')
    print(f'Added {new_pg_added} PG items')

    print("\n=== 3. Adding missing TS items ===")
    existing_ts_codes = set(t['code'] for t in ts_all)
    new_ts_added = 0

    for mr in map_ref:
        for ts_name in mr['ts_names']:
            # Search TS lookup for this name
            found = False
            for code, item in ts_lookup.items():
                if ts_name in item['name'] or item['name'] in ts_name or \
                   clean(ts_name) == clean(item['name']):
                    if code not in existing_ts_codes:
                        ts_all.append({
                            'id': f'ts_{len(ts_all)}',
                            'code': code,
                            'name': item['name'],
                            'desc': item.get('desc', ''),
                        })
                        existing_ts_codes.add(code)
                        new_ts_added += 1
                        print(f'  Added TS: {code} | {item["name"]}')
                    found = True
                    break

            if not found:
                # Try fuzzy match
                best_score = 0
                best_item = None
                for code, item in ts_lookup.items():
                    score = SequenceMatcher(None, clean(ts_name), clean(item['name'])).ratio()
                    if score > best_score:
                        best_score = score
                        best_item = (code, item)

                if best_score > 0.7 and best_item:
                    code, item = best_item
                    if code not in existing_ts_codes:
                        ts_all.append({
                            'id': f'ts_{len(ts_all)}',
                            'code': code,
                            'name': item['name'],
                            'desc': item.get('desc', ''),
                        })
                        existing_ts_codes.add(code)
                        new_ts_added += 1
                        print(f'  Added TS (fuzzy {best_score:.2f}): {code} | {item["name"]}')
                else:
                    print(f'  [NOT FOUND] TS: {ts_name}')
    print(f'Added {new_ts_added} TS items')

    print("\n=== 4. Removing ALL old obstetric cross-refs ===")
    ob_sh_codes = set()
    for mr in map_ref:
        for sh_name in mr['sh_names']:
            ob_sh_codes.add(sh_name)

    # Also mark 013314 codes as OB
    before = len(cross_refs)
    removed_old = 0
    removed_new = 0
    keep = []
    for r in cross_refs:
        sc = r.get('sh_code', '')
        if sc.startswith('013314'):
            removed_new += 1
            continue
        # Check if this is an OB-related cross-ref by pg_category
        if r.get('pg_category') == '产科类':
            removed_old += 1
            continue
        keep.append(r)

    cross_refs = keep
    print(f'Removed {removed_old} old OB refs + {removed_new} new OB refs')
    print(f'Remaining refs: {len(cross_refs)}')

    print("\n=== 5. Building comprehensive cross-refs ===")

    # Build lookup dictionaries
    pg_by_name = {}
    for p in pg_all:
        pg_by_name[clean(p['name'])] = p

    # Build TS lookup
    ts_by_name = {}
    ts_by_code = {}
    for t in ts_all:
        ts_by_code[t['code']] = t
        ts_by_name[clean(t['name'])] = t

    # Helper: add TS items
    def find_ts_items(ts_names_list):
        """Find TS items by name from the reference list. Create if not exists in by_name."""
        result = []
        for ts_name in ts_names_list:
            cname = clean(ts_name)
            # Try exact
            if cname in ts_by_name:
                result.append(ts_by_name[cname])
                continue
            # Try fuzzy in ts_lookup
            best = None
            best_score = 0
            for code, item in ts_lookup.items():
                score = SequenceMatcher(None, cname, clean(item['name'])).ratio()
                if score > best_score:
                    best_score = score
                    best = (code, item)
            if best and best_score > 0.65:
                code = best[0]
                if code in ts_by_code:
                    result.append(ts_by_code[code])
                    continue
        return result

    def find_sh_items(sh_names_list, sh_list):
        """Find old SH items by name"""
        result = []
        for sh_name in sh_names_list:
            cname = clean(sh_name)
            idx, score = fuzzy_match(sh_name, sh_list, 'name', threshold=0.5)
            if idx >= 0:
                result.append(sh_list[idx])
            else:
                print(f'  [SKIP SH] {sh_name}')
        return result

    def add_ref(sid, sname, scode, pg, ts_item, icd9_code='', icd9_name=''):
        ref = {
            'sh_id': sid, 'sh_name': sname, 'sh_code': scode,
            'pg_id': pg['id'], 'pg_name': pg['name'], 'pg_seq': pg['seq'], 'pg_category': pg['category'],
            'ts_id': ts_item['id'] if ts_item else '',
            'ts_name': ts_item['name'] if ts_item else '',
            'ts_code': ts_item['code'] if ts_item else '',
            'icd9_id': '', 'icd9_name': icd9_name, 'icd9_code': icd9_code,
            'sh_pg_score': '0.95', 'pg_ts_score': '1.00' if ts_item else '',
        }
        cross_refs.append(ref)

    new_refs = 0

    # Build mapping: PG name -> old SH items list (to avoid duplicate fuzzy matches)
    # First, collect all old SH matches
    pg_old_sh_map = {}
    for mr in map_ref:
        pg_name = mr['pg_name']
        if pg_name not in pg_old_sh_map:
            sh_items = find_sh_items(mr['sh_names'], sh_all)
            pg_old_sh_map[pg_name] = sh_items

    # Now build cross-refs: for each PG, link old SH + TS
    for mr in map_ref:
        pg_name = mr['pg_name']
        cname = clean(pg_name)
        if cname not in pg_by_name:
            print(f'[SKIP] PG not found: {pg_name}')
            continue

        pg = pg_by_name[cname]
        ts_items = find_ts_items(mr['ts_names'])

        # ICD-9 lookup
        icd9_code = ''
        icd9_name = ''
        for kw, (code, name) in ob_icd9_map.items():
            if kw in pg_name:
                icd9_code = code
                icd9_name = name
                break

        # Link old SH items to this PG
        old_sh_items = pg_old_sh_map.get(pg_name, [])
        for sh in old_sh_items:
            if ts_items:
                for ts in ts_items:
                    add_ref(sh['id'], sh['name'], sh['code'], pg, ts, icd9_code, icd9_name)
                    new_refs += 1
            else:
                add_ref(sh['id'], sh['name'], sh['code'], pg, None, icd9_code, icd9_name)
                new_refs += 1

    # Link new SH items to their PG
    # Map new SH items to PG names (same mapping as before)
    new_sh_to_pg = {
        'sh_4935': '阴道分娩（常规）', 'sh_4936': '阴道分娩（常规）', 'sh_4937': '阴道分娩（常规）',
        'sh_4938': '阴道分娩（复杂）', 'sh_4939': '阴道分娩（复杂）', 'sh_4940': '阴道分娩（复杂）',
        'sh_4942': '剖宫产（复杂）', 'sh_4943': '剖宫产（复杂）', 'sh_4944': '剖宫产（复杂）',
        'sh_4945': '宫颈环扎术（常规）', 'sh_4946': '宫颈环扎术（常规）',
        'sh_4947': '宫颈环扎术（特殊）', 'sh_4948': '宫颈环扎术（特殊）',
        'sh_4949': '手术减胎',
    }

    for sh_item in sh_new:
        sid = sh_item['id']
        if sid not in new_sh_to_pg:
            continue

        pg_name = new_sh_to_pg[sid]
        pg = pg_by_name.get(clean(pg_name))
        if not pg:
            print(f'[SKIP] PG for new SH: {pg_name}')
            continue

        # Find TS items for this PG
        ts_items_for_pg = []
        for mr in map_ref:
            if mr['pg_name'] == pg_name:
                ts_items_for_pg = find_ts_items(mr['ts_names'])
                break

        # ICD-9
        icd9_code = ''
        icd9_name = ''
        for kw, (code, name) in ob_icd9_map.items():
            if kw in pg_name:
                icd9_code = code
                icd9_name = name
                break

        if ts_items_for_pg:
            for ts in ts_items_for_pg:
                add_ref(sid, sh_item['name'], sh_item['code'], pg, ts, icd9_code, icd9_name)
                new_refs += 1
        else:
            add_ref(sid, sh_item['name'], sh_item['code'], pg, None, icd9_code, icd9_name)
            new_refs += 1

    print(f'Created {new_refs} new cross-refs')

    print("\n=== 6. Rebuilding index ===")
    sh_idx = {}; pg_idx = {}; ts_idx = {}; icd9_idx = {}
    for i, ref in enumerate(cross_refs):
        if ref['sh_id']: sh_idx.setdefault(ref['sh_id'], []).append(i)
        if ref['pg_id']: pg_idx.setdefault(ref['pg_id'], []).append(i)
        if ref['ts_id']: ts_idx.setdefault(ref['ts_id'], []).append(i)
        if ref['icd9_id']: icd9_idx.setdefault(ref['icd9_id'], []).append(i)

    data['shanghai'] = sh_all
    data['shanghai_new'] = sh_new
    data['pricing_guide'] = pg_all
    data['tech_specs'] = ts_all
    data['icd9'] = icd9_all
    data['cross_refs'] = cross_refs
    data['_index'] = {'sh': sh_idx, 'pg': pg_idx, 'ts': ts_idx, 'icd9': icd9_idx}

    dc = data['stats']
    dc['shanghai_count'] = len(sh_all)
    dc['shanghai_new_count'] = len(sh_new)
    dc['pricing_guide_count'] = len(pg_all)
    dc['tech_specs_count'] = len(ts_all)
    dc['icd9_count'] = len(icd9_all)
    dc['cross_refs_count'] = len(cross_refs)
    dc['shanghai_matched'] = sum(1 for r in cross_refs if r['pg_id'])
    dc['full_chain'] = sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id'])

    print("\n=== 7. Saving ===")
    with open(f'{BASE}/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    with gzip.open(f'{BASE}/data.json.gz', 'wb', compresslevel=6) as f:
        f.write(jbytes)

    print(f'\n=== RESULTS ===')
    print(f'  PG items: {len(pg_all)}')
    print(f'  TS items: {len(ts_all)}')
    print(f'  Cross-refs: {len(cross_refs)}')
    print(f'  SH matched: {dc["shanghai_matched"]}')
    print(f'  Full chain (SH+PG+TS+ICD9): {dc["full_chain"]}')
    print(f'  File size: {len(jbytes)} bytes')
    print('Done!')

if __name__ == '__main__':
    main()
