"""
Complete rebuild of rehab 4-way mappings based on:
上海市康复类医疗服务价格项目立项指南映射关系（参考）.xlsx

Parses HTML-format Excel directly to handle <br/> tags correctly.
Items separated by <br/> are distinct; <br/> from word-wrapping is
disambiguated using known SH/TS/PG name lookup.
"""
import json, gzip, os, sys, io, re, pandas as pd
from difflib import SequenceMatcher

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.dirname(BASE)

def clean(s):
    return s.replace('\n','').replace(' ','').replace('（','(').replace('）',')').replace(';','').strip()

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

def split_br_cell(cell_html, known_names):
    """Split a <td> cell by <br/> tags, using known_names to distinguish
    item separators from Excel word-wrapping within a single long name."""
    if not cell_html:
        return []
    # Split by <br> or <br/> tags
    parts = re.split(r'<br[^>]*/?>', cell_html)
    tokens = []
    for p in parts:
        text = re.sub(r'<[^>]+>', '', p).strip()
        if text:
            tokens.append(text)
    if not tokens:
        return []

    result = []
    i = 0
    while i < len(tokens):
        cn = clean(tokens[i])
        # If single token matches known name, it's a complete item
        if cn in known_names:
            result.append(tokens[i])
            i += 1
            continue

        # Doesn't match alone — try merging with consecutive tokens
        found_merge = False
        # Try longest match first (up to 3 tokens)
        for j in range(min(i + 3, len(tokens)), i + 1, -1):
            combined = ''.join(tokens[i:j])
            if clean(combined) in known_names:
                result.append(combined)
                i = j
                found_merge = True
                break

        if not found_merge:
            # No known-name match — keep as individual token
            # (may be a genuine new item not in our lookup)
            result.append(tokens[i])
            i += 1

    return result

def main():
    print("=== 1. Loading data ===")
    with open(f'{BASE}/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    sh_all = data['shanghai']
    sh_new = data['shanghai_new']
    pg_all = data['pricing_guide']
    ts_all = data['tech_specs']
    cross_refs = data['cross_refs']

    # Load full TS source
    xls = pd.ExcelFile(f'{BUILDER}/全国医疗服务项目技术规范--2023全.xlsx')
    ts_lookup = {}
    for sheet_idx in range(len(xls.sheet_names)):
        try:
            df = pd.read_excel(xls, sheet_name=sheet_idx)
            for idx, row in df.iterrows():
                code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                if not code or len(code) < 6: continue
                name_cn = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
                desc = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
                if name_cn and code not in ts_lookup:
                    ts_lookup[code] = {'code': code, 'name': name_cn, 'desc': desc[:300]}
        except:
            pass
    print(f'TS source items: {len(ts_lookup)}')

    # Build known-names set for <br/> disambiguation BEFORE parsing
    print("\n=== 2. Building known-names lookup ===")
    known_names = set()
    for s in sh_all:
        known_names.add(clean(s['name']))
    for t in ts_all:
        known_names.add(clean(t['name']))
        known_names.add(clean(t['name']).replace('(', '').replace(')', ''))
    for code, item in ts_lookup.items():
        known_names.add(clean(item['name']))
        known_names.add(clean(item['name']).replace('(', '').replace(')', ''))
    print(f'Known names: {len(known_names)}')

    # Parse rehab mapping reference using raw HTML (preserves <br/> tags)
    print("\n=== 3. Parsing mapping reference (HTML with <br/> splitting) ===")
    map_file = f'{BUILDER}/上海市康复类医疗服务价格项目立项指南映射关系（参考）.xlsx'
    with open(map_file, 'r', encoding='utf-8') as fh:
        html_content = fh.read()

    # Extract table and rows
    table_match = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL)
    if not table_match:
        print("ERROR: Could not find table in HTML")
        sys.exit(1)

    row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_match.group(1), re.DOTALL)
    print(f'Found {len(row_matches)} table rows')

    # Extract cells from each row
    all_rows = []
    for row_html in row_matches:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        all_rows.append(cells)

    # Parse: each mapping item = N rows (main + continuation rows without seq number)
    # "训练" items: 3 rows (main + surcharge + AI), "检查" items: 2 rows (main + AI)
    # Strategy: find next row with a digit in col0 as the boundary between items
    # First 2 rows are headers, data starts at row index 2 (0-based)
    map_ref = []
    i = 2  # skip header rows
    while i < len(all_rows):
        cells = all_rows[i]
        if len(cells) < 2:
            i += 1
            continue

        seq = re.sub(r'<[^>]+>', '', cells[0]).strip() if cells else ''
        if not seq or not seq.isdigit():
            i += 1
            continue

        pg_name = re.sub(r'<[^>]+>', '', cells[1]).strip() if len(cells) > 1 else ''

        def parse_cell(row_idx, col_idx):
            """Extract items from a specific cell using <br/>-aware splitting."""
            if col_idx < len(all_rows[row_idx]):
                return split_br_cell(all_rows[row_idx][col_idx], known_names)
            return []

        # Parse main row (cols 4-7 = old SH direct, old SH into-price, TS direct, TS into-price)
        sh_names = parse_cell(i, 4)
        sh_into_names = parse_cell(i, 5)
        ts_names = parse_cell(i, 6)
        ts_into_names = parse_cell(i, 7)

        # Collect continuation rows until next main row (with seq number in col0)
        # Continuation rows only have data in cols 5 (SH into-price) and 7 (TS into-price)
        next_i = i + 1
        while next_i < len(all_rows):
            ncells = all_rows[next_i]
            if ncells and len(ncells) > 0:
                nseq = re.sub(r'<[^>]+>', '', ncells[0]).strip()
                if nseq and nseq.isdigit():
                    break  # Found next main row
            # Continuation row — parse cols 5 and 7
            sh_into_names.extend(parse_cell(next_i, 5))
            ts_into_names.extend(parse_cell(next_i, 7))
            next_i += 1

        if pg_name:
            map_ref.append({
                'seq': seq, 'pg_name': pg_name,
                'sh_names': sh_names,
                'sh_into_names': sh_into_names,
                'ts_names': ts_names,
                'ts_into_names': ts_into_names,
            })

        i = next_i  # Move to next main row

    print(f'Parsed {len(map_ref)} rehab mapping items')
    for mr in map_ref:
        seq = mr['seq']
        pg = mr['pg_name'][:40]
        sh_cnt = len(mr['sh_names'])
        sh_in = len(mr['sh_into_names'])
        ts_cnt = len(mr['ts_names'])
        ts_in = len(mr['ts_into_names'])
        print(f'  #{seq}: {pg} | SH:{sh_cnt}+{sh_in} TS:{ts_cnt}+{ts_in}')

    # PG name normalization - map PG data names to reference names
    pg_name_map = {
        '认知功能训练': '认知功能障碍训练',
        '吞咽功能训练': '吞咽功能障碍训练',
        '言语功能训练': '言语功能障碍训练',
        '认知功能检查': '认知功能障碍检查',
    }

    print("\n=== 4. Fixing PG items ===")
    # Fix/rename existing PG items
    for p in pg_all:
        if p['name'] in pg_name_map:
            old = p['name']
            p['name'] = pg_name_map[old]
            nm = p['name']
            print(f'  Renamed: {old} -> {nm}')

    # Add missing PG items
    ref_names = set(mr['pg_name'] for mr in map_ref)
    existing_names = set(p['name'] for p in pg_all)
    new_pg = 0
    for mr in map_ref:
        if mr['pg_name'] not in existing_names:
            mr_seq = mr['seq']
            mr_pg_name = mr['pg_name']
            seq_str = f'55{int(mr_seq):d}' if mr_seq.isdigit() else mr_seq
            pg_all.append({
                'id': f'pg_{len(pg_all)}',
                'seq': seq_str,
                'category': '康复类',
                'name': mr_pg_name,
                'output': '',
                'cost_structure': '',
                'unit': '次',
            })
            existing_names.add(mr_pg_name)
            new_pg += 1
            print(f'  Added PG: {mr_pg_name}')
    print(f'Added {new_pg} PG items. Total: {len(pg_all)}')

    print("\n=== 5. Adding missing TS items ===")
    existing_ts_codes = set(t['code'] for t in ts_all)
    new_ts = 0

    for mr in map_ref:
        all_ts = mr['ts_names'] + mr['ts_into_names']
        for ts_name in all_ts:
            if not ts_name: continue
            cname = clean(ts_name)
            # Check if already in ts_all
            found = False
            for t in ts_all:
                if clean(t['name']) == cname:
                    found = True
                    break
            if found: continue

            # Search full TS source
            for code, item in ts_lookup.items():
                if clean(item['name']) == cname:
                    ts_all.append({
                        'id': f'ts_{len(ts_all)}',
                        'code': code, 'name': item['name'], 'desc': item.get('desc', ''),
                    })
                    existing_ts_codes.add(code)
                    new_ts += 1
                    break
            else:
                # Fuzzy
                best_score = 0
                best_item = None
                for code, item in ts_lookup.items():
                    score = SequenceMatcher(None, cname, clean(item['name'])).ratio()
                    if score > best_score:
                        best_score = score
                        best_item = (code, item)
                if best_score > 0.7 and best_item:
                    code, item = best_item
                    if code not in existing_ts_codes:
                        ts_all.append({
                            'id': f'ts_{len(ts_all)}',
                            'code': code, 'name': item['name'], 'desc': item.get('desc', ''),
                        })
                        existing_ts_codes.add(code)
                        new_ts += 1
    print(f'Added {new_ts} TS items. Total: {len(ts_all)}')

    print("\n=== 6. Removing old rehab cross-refs ===")
    before = len(cross_refs)
    cross_refs = [r for r in cross_refs if r.get('pg_category') != '康复类']
    removed = before - len(cross_refs)
    print(f'Removed {removed} rehab cross-refs. Remaining: {len(cross_refs)}')

    # Also remove old 015* new SH refs
    before2 = len(cross_refs)
    cross_refs = [r for r in cross_refs if not r.get('sh_code','').startswith('015')]
    removed2 = before2 - len(cross_refs)
    print(f'Removed {removed2} new rehab refs. Remaining: {len(cross_refs)}')

    print("\n=== 7. Adding ICD-9 items for rehab ===")
    icd9_all = data['icd9']
    icd9_by_code = {}
    for icd in icd9_all:
        yb_code = icd.get('yb_code', '')
        if yb_code:
            icd9_by_code[yb_code] = icd

    # Ensure rehab ICD-9 codes exist in the data
    rehab_icd9_codes = {
        '93.3900x002': '物理疗法',
        '93.3900x003': '物理疗法-辅具/生活/职业',
        '93.3900x004': '物理疗法-神经发育',
        '93.3800x001': '康复评定',
    }
    for code, desc in rehab_icd9_codes.items():
        if code not in icd9_by_code:
            new_icd9 = {
                'id': f'icd9_{len(icd9_all)}',
                'yb_code': code,
                'yb_name': desc,
                'gl_code': code,
                'gl_name': desc,
            }
            icd9_all.append(new_icd9)
            icd9_by_code[code] = new_icd9
            print(f'  Added ICD-9: {code} | {desc}')
    data['icd9'] = icd9_all

    # Map PG name → ICD-9 code
    rehab_icd9_map = {
        '意识功能训练': '93.3900x002',
        '认知功能障碍训练': '93.3900x002',
        '吞咽功能障碍训练': '93.3900x002',
        '言语功能障碍训练': '93.3900x002',
        '运动功能障碍训练': '93.3900x002',
        '脏器功能障碍训练': '93.3900x002',
        '辅助器具使用训练': '93.3900x003',
        '生活技能康复训练': '93.3900x003',
        '职业技能康复训练': '93.3900x003',
        '神经发育障碍康复训练（个体）': '93.3900x004',
        '神经发育障碍康复训练（团体）': '93.3900x004',
        '认知功能障碍检查': '93.3800x001',
        '吞咽功能障碍检查': '93.3800x001',
        '言语功能障碍检查': '93.3800x001',
        '运动功能障碍检查': '93.3800x001',
        '脏器功能障碍检查': '93.3800x001',
        '神经发育障碍检查': '93.3800x001',
    }

    print("\n=== 8. Building comprehensive cross-refs ===")
    # Build lookups
    pg_by_name = {clean(p['name']): p for p in pg_all}
    ts_by_name = {clean(t['name']): t for t in ts_all}

    new_refs = 0

    for mr in map_ref:
        pg_name = mr['pg_name']
        pg_key = clean(pg_name)
        if pg_key not in pg_by_name:
            print(f'  [SKIP] PG not found: {pg_name}')
            continue
        pg = pg_by_name[pg_key]

        # ICD-9 lookup
        icd9_code = rehab_icd9_map.get(pg_name, '')
        icd9_id = ''
        icd9_name = ''
        if icd9_code and icd9_code in icd9_by_code:
            icd9_item = icd9_by_code[icd9_code]
            icd9_id = icd9_item['id']
            icd9_name = icd9_item.get('yb_name', '')

        # Collect TS items from direct + into-price (track source)
        ts_direct_names = set(clean(n) for n in mr['ts_names'])
        ts_items = []  # list of (item, source) tuples
        for ts_name in mr['ts_names']:
            cname = clean(ts_name)
            if cname in ts_by_name:
                ts_items.append((ts_by_name[cname], 'direct'))
            else:
                best_score = 0; best_t = None
                for c, t in ts_by_name.items():
                    score = SequenceMatcher(None, cname, c).ratio()
                    if score > best_score: best_score, best_t = score, t
                if best_score > 0.7 and best_t:
                    ts_items.append((best_t, 'direct'))
        for ts_name in mr['ts_into_names']:
            cname = clean(ts_name)
            if cname in ts_by_name:
                ts_items.append((ts_by_name[cname], 'into_price'))
            else:
                best_score = 0; best_t = None
                for c, t in ts_by_name.items():
                    score = SequenceMatcher(None, cname, c).ratio()
                    if score > best_score: best_score, best_t = score, t
                if best_score > 0.7 and best_t:
                    ts_items.append((best_t, 'into_price'))

        # Find old SH items from direct + into-price (track source)
        sh_direct_names = set(clean(n) for n in mr['sh_names'])
        sh_items = []  # list of (item, source) tuples
        for sh_name in mr['sh_names']:
            idx, score = fuzzy_match(sh_name, sh_all, 'name', threshold=0.55)
            if idx >= 0:
                sh_items.append((sh_all[idx], 'direct'))
        for sh_name in mr['sh_into_names']:
            idx, score = fuzzy_match(sh_name, sh_all, 'name', threshold=0.55)
            if idx >= 0:
                sh_items.append((sh_all[idx], 'into_price'))

        # Create cross-refs for old SH
        for sh, sh_src in sh_items:
            if ts_items:
                for ts, ts_src in ts_items:
                    cross_refs.append({
                        'sh_id': sh['id'], 'sh_name': sh['name'], 'sh_code': sh['code'],
                        'pg_id': pg['id'], 'pg_name': pg_name, 'pg_seq': pg['seq'], 'pg_category': pg['category'],
                        'ts_id': ts['id'], 'ts_name': ts['name'], 'ts_code': ts['code'],
                        'icd9_id': icd9_id, 'icd9_name': icd9_name, 'icd9_code': icd9_code,
                        'sh_pg_score': '0.95', 'pg_ts_score': '1.00',
                        'sh_source': sh_src, 'ts_source': ts_src,
                    })
                    new_refs += 1
            else:
                cross_refs.append({
                    'sh_id': sh['id'], 'sh_name': sh['name'], 'sh_code': sh['code'],
                    'pg_id': pg['id'], 'pg_name': pg_name, 'pg_seq': pg['seq'], 'pg_category': pg['category'],
                    'ts_id': '', 'ts_name': '', 'ts_code': '',
                    'icd9_id': icd9_id, 'icd9_name': icd9_name, 'icd9_code': icd9_code,
                    'sh_pg_score': '0.95', 'pg_ts_score': '',
                    'sh_source': sh_src, 'ts_source': '',
                })
                new_refs += 1

        # Link new SH items to PG
        # Map by name: new SH name (去掉扩展标识) -> PG name
        for s in sh_new:
            sname = clean(s['name'])
            # Strip extension suffixes
            base_name = sname.replace('(扩展)','').replace('（扩展）','').replace('-人工智能辅助训练','').replace('-人工智能辅助检查','')
            base_name = base_name.replace('-会阴裂伤修补（限3-4度）（加收）','').replace('-宫颈裂伤修补（加收）','').replace('-内镜下辅助操作（加收）','')
            base_name = base_name.replace('-每增加10分钟加收','').replace('-运动功能训练（水中）','')

            # Normalize: 认知功能检查 -> 认知功能障碍检查
            for old_n, new_n in pg_name_map.items():
                base_name = base_name.replace(clean(old_n).replace('(','').replace(')',''), clean(new_n).replace('(','').replace(')',''))

            if base_name == pg_key or base_name in pg_key or pg_key in base_name:
                if ts_items:
                    for ts, ts_src in ts_items:
                        cross_refs.append({
                            'sh_id': s['id'], 'sh_name': s['name'], 'sh_code': s['code'],
                            'pg_id': pg['id'], 'pg_name': pg_name, 'pg_seq': pg['seq'], 'pg_category': pg['category'],
                            'ts_id': ts['id'], 'ts_name': ts['name'], 'ts_code': ts['code'],
                            'icd9_id': icd9_id, 'icd9_name': icd9_name, 'icd9_code': icd9_code,
                            'sh_pg_score': '0.95', 'pg_ts_score': '1.00',
                            'sh_source': 'direct', 'ts_source': ts_src,
                        })
                        new_refs += 1
                else:
                    cross_refs.append({
                        'sh_id': s['id'], 'sh_name': s['name'], 'sh_code': s['code'],
                        'pg_id': pg['id'], 'pg_name': pg_name, 'pg_seq': pg['seq'], 'pg_category': pg['category'],
                        'ts_id': '', 'ts_name': '', 'ts_code': '',
                        'icd9_id': icd9_id, 'icd9_name': icd9_name, 'icd9_code': icd9_code,
                        'sh_pg_score': '0.95', 'pg_ts_score': '',
                        'sh_source': 'direct', 'ts_source': '',
                    })
                    new_refs += 1

    print(f'Created {new_refs} new cross-refs')

    print("\n=== 9. Rebuilding index ===")
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
    data['cross_refs'] = cross_refs
    data['_index'] = {'sh': sh_idx, 'pg': pg_idx, 'ts': ts_idx, 'icd9': icd9_idx}

    dc = data['stats']
    dc['shanghai_count'] = len(sh_all)
    dc['shanghai_new_count'] = len(sh_new)
    dc['pricing_guide_count'] = len(pg_all)
    dc['tech_specs_count'] = len(ts_all)
    dc['icd9_count'] = len(data['icd9'])
    dc['cross_refs_count'] = len(cross_refs)
    dc['shanghai_matched'] = sum(1 for r in cross_refs if r['pg_id'])
    dc['full_chain'] = sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id'])

    print("\n=== 10. Saving ===")
    with open(f'{BASE}/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    with gzip.open(f'{BASE}/data.json.gz', 'wb', compresslevel=6) as f:
        f.write(jbytes)

    print(f'\n=== RESULTS ===')
    print(f'  PG items: {len(pg_all)}')
    print(f'  TS items: {len(ts_all)}')
    print(f'  Cross-refs: {len(cross_refs)}')
    print(f'  New refs created: {new_refs}')
    print(f'  SH matched: {dc["shanghai_matched"]}')
    print(f'  Full chain: {dc["full_chain"]}')
    print(f'  File size: {len(jbytes)} bytes')
    print('Done!')

if __name__ == '__main__':
    main()
