"""
Sync rehabilitation mappings from 2 files:
1. 上海市康复类医疗服务价格项目立项指南映射关系（参考）.xlsx
2. 关于规范调整本市康复类医疗服务价格项目的通知.xlsx
"""
import json, gzip, os, pandas as pd
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.dirname(BASE)

def clean(s):
    return s.replace('\n','').replace(' ','').replace('（','(').replace('）',')').strip()

def fuzzy_match(target, candidates, key='name', threshold=0.5):
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
    print("=== Loading rehab mapping reference ===")
    map_file = os.path.join(BUILDER, '上海市康复类医疗服务价格项目立项指南映射关系（参考）.xlsx')
    t_map = pd.read_html(map_file, encoding='utf-8')[0]

    # Parse: rows 3+ are data, every 3 rows = one mapping item (main, 加收, 扩展)
    mappings = []
    i = 3  # Skip headers
    while i < len(t_map):
        seq = str(t_map.iloc[i, 0]).strip() if pd.notna(t_map.iloc[i, 0]) else ''
        if not seq:
            i += 1
            continue

        pg_name = str(t_map.iloc[i, 1]).strip() if pd.notna(t_map.iloc[i, 1]) else ''
        pg_surcharge = str(t_map.iloc[i, 2]).strip() if pd.notna(t_map.iloc[i, 2]) else ''
        pg_extension = str(t_map.iloc[i, 3]).strip() if pd.notna(t_map.iloc[i, 3]) else ''
        sh_names = str(t_map.iloc[i, 4]).strip() if pd.notna(t_map.iloc[i, 4]) else ''
        sh_into_price = str(t_map.iloc[i, 5]).strip() if pd.notna(t_map.iloc[i, 5]) else ''
        ts_names = str(t_map.iloc[i, 6]).strip() if pd.notna(t_map.iloc[i, 6]) else ''
        ts_into_price = str(t_map.iloc[i, 7]).strip() if pd.notna(t_map.iloc[i, 7]) else ''

        # Next rows may have surcharge/extension variant info
        surcharge_info = ''
        extension_info = ''
        if i+1 < len(t_map) and pd.notna(t_map.iloc[i+1, 2]) and str(t_map.iloc[i+1, 2]).strip():
            surcharge_info = str(t_map.iloc[i+1, 2]).strip()
        if i+2 < len(t_map) and pd.notna(t_map.iloc[i+2, 3]) and str(t_map.iloc[i+2, 3]).strip():
            extension_info = str(t_map.iloc[i+2, 3]).strip()

        mappings.append({
            'seq': seq,
            'pg_name': pg_name,
            'pg_surcharge': surcharge_info,
            'pg_extension': extension_info,
            'sh_names': [s.strip() for s in sh_names.split('\n') if s.strip()],
            'sh_into_price': [s.strip() for s in sh_into_price.split('\n') if s.strip()],
            'ts_names': [s.strip() for s in ts_names.split('\n') if s.strip()],
            'ts_into_price': [s.strip() for s in ts_into_price.split('\n') if s.strip()],
        })

        # Skip to next item (3-row blocks)
        i += 3
        # Skip any empty continuation rows
        while i < len(t_map):
            s = str(t_map.iloc[i, 0]).strip() if pd.notna(t_map.iloc[i, 0]) else ''
            if s:
                break
            # Check if it's a continuation with surcharge/extension data
            has_data = any(pd.notna(t_map.iloc[i, c]) and str(t_map.iloc[i, c]).strip()
                          for c in [2, 3, 5, 7])
            if has_data:
                # Continuation row - merge into previous mapping
                prev = mappings[-1]
                add_sh = str(t_map.iloc[i, 4]).strip() if pd.notna(t_map.iloc[i, 4]) else ''
                add_ts = str(t_map.iloc[i, 6]).strip() if pd.notna(t_map.iloc[i, 6]) else ''
                if add_sh: prev['sh_into_price'].extend([s.strip() for s in add_sh.split('\n') if s.strip()])
                if add_ts: prev['ts_into_price'].extend([s.strip() for s in add_ts.split('\n') if s.strip()])
                i += 1
            else:
                i += 1

    print(f'Parsed {len(mappings)} rehab mapping items')

    # === Load notice (new Shanghai rehab prices) ===
    print("\n=== Loading rehab notice (new prices) ===")
    notice_file = os.path.join(BUILDER, '关于规范调整本市康复类医疗服务价格项目的通知.xlsx')
    t_notice = pd.read_html(notice_file, encoding='utf-8')[0]

    new_sh_items = []
    for _, row in t_notice.iterrows():
        seq = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        code = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        name = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
        if not seq or len(code) < 8:
            # Skip category headers and empty rows
            if '使用说明' in name or '康复评定' == name or '康复治疗' == name:
                continue
            if not code:
                continue

        desc = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
        cost = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
        unit = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ''
        price = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ''
        notes = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ''
        payment = str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else ''

        if code and name and price:
            new_sh_items.append({
                'seq': seq,
                'code': code,
                'name': name,
                'desc': desc[:300],
                'unit': unit,
                'price': price,
                'notes': notes,
                'payment': payment,
            })

    print(f'Loaded {len(new_sh_items)} new Shanghai rehab items')

    # === Load current data ===
    with open(os.path.join(BASE, 'data.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)

    sh_all = data['shanghai']
    sh_new = data['shanghai_new']
    pg_all = data['pricing_guide']
    ts_all = data['tech_specs']
    cross_refs = data['cross_refs']

    # === Add new rehab items to shanghai_new ===
    added_sh = 0
    for item in new_sh_items:
        exists = any(s['code'] == item['code'] for s in sh_new)
        if not exists:
            sid = f'sh_{len(sh_all) + len(sh_new)}'
            sh_new.append({
                'id': sid,
                'code': item['code'],
                'name': item['name'],
                'desc': item['desc'],
                'unit': item['unit'],
                'price': item['price'],
                'notes': item['notes'],
            })
            added_sh += 1
    print(f'\nAdded {added_sh} new Shanghai rehab items')

    # === Name aliases to fix PG matching ===
    pg_aliases = {
        '运动功能障碍训练': '运动功能训练',
        '运动功能训练': '运动功能训练',
        '脏器功能障碍训练': '脏器功能训练',
        '辅助器具使用训练': '辅助器具使用训练',
        '吞咽功能障碍检查': '吞咽功能检查',
        '言语功能障碍检查': '言语功能检查',
        '生活技能康复训练': '生活技能康复训练',
        '运动功能障碍检查': '运动功能检查',
        '神经发育障碍检查': '神经发育障碍检查',
        '职业技能康复训练': '职业技能康复训练',
        '神经发育障碍康复训练（个体）': '神经发育障碍康复训练（个体）',
        '神经发育障碍康复训练（团体）': '神经发育障碍康复训练（团体）',
    }

    # Add missing PG items that exist in the main guide
    rehab_pg_items = {
        '意识功能训练': ('536', '康复类', '意识功能训练'),
        '认知功能训练': ('537', '康复类', '认知功能训练'),
        '吞咽功能训练': ('538', '康复类', '吞咽功能训练'),
        '言语功能训练': ('539', '康复类', '言语功能训练'),
        '职业技能康复训练': ('544', '康复类', '职业技能康复训练'),
        '神经发育障碍康复训练（个体）': ('545', '康复类', '神经发育障碍康复训练（个体）'),
        '认知功能检查': ('547', '康复类', '认知功能检查'),
        '运动功能检查': ('373', '口腔类', '颌面运动功能检查'),
    }

    # === Build cross-refs from mapping ===
    new_refs = 0
    updated_refs = 0

    for mm in mappings:
        pg_name = mm['pg_name']
        if not pg_name:
            continue

        # Find PG item - try exact alias first
        pg_name_clean = pg_name.replace('\n','').strip()
        alias = pg_aliases.get(pg_name_clean, pg_name_clean)

        pg_idx, pg_score = fuzzy_match(alias, pg_all, 'name', threshold=0.5)

        # If not found but in rehab_pg_items, add it
        if pg_idx < 0 and alias in rehab_pg_items:
            info = rehab_pg_items[alias]
            new_pg = {
                'id': f'pg_{len(pg_all)}',
                'seq': info[0],
                'category': info[1],
                'name': alias,
                'output': '',
                'cost_structure': '',
                'unit': '次',
            }
            pg_all.append(new_pg)
            pg_idx = len(pg_all) - 1
            pg_score = 1.0
            print(f'  Added PG: {alias}')

        if pg_idx < 0:
            print(f'  [SKIP PG] {pg_name} (searched: {alias})')
            continue

        pg = pg_all[pg_idx]
        print(f'[OK] {pg_name} -> PG:{pg["name"]}')

        # Find TS items
        ts_matches = []
        for ts_name in mm['ts_names']:
            ts_idx, ts_score = fuzzy_match(ts_name, ts_all, 'name', threshold=0.5)
            if ts_idx >= 0:
                ts_matches.append({
                    'id': ts_all[ts_idx]['id'],
                    'code': ts_all[ts_idx]['code'],
                    'name': ts_all[ts_idx]['name'],
                    'score': ts_score,
                })

        # For each old Shanghai price name, find match
        for sh_name in mm['sh_names']:
            # Search in both shanghai and shanghai_new
            sh_idx, sh_score = fuzzy_match(sh_name, sh_all, 'name', threshold=0.55)
            if sh_idx < 0:
                # Try shanghai_new
                sh_idx, sh_score = fuzzy_match(sh_name, sh_new, 'name', threshold=0.55)
                if sh_idx >= 0:
                    sh = sh_new[sh_idx]
                else:
                    print(f'  [SKIP SH] {sh_name}')
                    continue
            else:
                sh = sh_all[sh_idx]

            ts_id = ts_matches[0]['id'] if ts_matches else ''
            ts_code = ts_matches[0]['code'] if ts_matches else ''
            ts_name_m = ts_matches[0]['name'] if ts_matches else ''
            ts_s = f'{ts_matches[0]["score"]:.2f}' if ts_matches else ''

            ref = {
                'sh_id': sh['id'],
                'sh_name': sh['name'],
                'sh_code': sh['code'],
                'pg_id': pg['id'],
                'pg_name': pg_name,
                'pg_seq': pg['seq'],
                'pg_category': pg['category'],
                'ts_id': ts_id,
                'ts_name': ts_name_m,
                'ts_code': ts_code,
                'icd9_id': '',
                'icd9_name': '',
                'icd9_code': '',
                'sh_pg_score': '0.95',
                'pg_ts_score': ts_s,
            }

            # Check for existing
            existing = None
            for i, r in enumerate(cross_refs):
                if r['sh_id'] == sh['id'] and r['pg_id'] == pg['id']:
                    existing = i
                    break

            if existing is not None:
                cross_refs[existing].update(ref)
                updated_refs += 1
            else:
                cross_refs.append(ref)
                new_refs += 1

            print(f'    SH: {sh_name} -> {sh["id"]}')

        # Also create refs for old SH items listed in 纳入价格构成
        for sh_name in mm['sh_into_price']:
            sh_idx, sh_score = fuzzy_match(sh_name, sh_all, 'name', threshold=0.5)
            if sh_idx < 0:
                continue
            sh = sh_all[sh_idx]
            ts_id = ts_matches[0]['id'] if ts_matches else ''
            ts_code = ts_matches[0]['code'] if ts_matches else ''
            ts_name_m = ts_matches[0]['name'] if ts_matches else ''
            ts_s = f'{ts_matches[0]["score"]:.2f}' if ts_matches else ''

            ref = {
                'sh_id': sh['id'],
                'sh_name': sh['name'],
                'sh_code': sh['code'],
                'pg_id': pg['id'],
                'pg_name': pg_name,
                'pg_seq': pg['seq'],
                'pg_category': pg['category'],
                'ts_id': ts_id,
                'ts_name': ts_name_m,
                'ts_code': ts_code,
                'icd9_id': '',
                'icd9_name': '',
                'icd9_code': '',
                'sh_pg_score': '0.95',
                'pg_ts_score': ts_s,
            }
            cross_refs.append(ref)
            new_refs += 1

    # === Rebuild index ===
    sh_idx_d = {}; pg_idx_d = {}; ts_idx_d = {}; icd9_idx_d = {}
    for i, ref in enumerate(cross_refs):
        if ref['sh_id']: sh_idx_d.setdefault(ref['sh_id'], []).append(i)
        if ref['pg_id']: pg_idx_d.setdefault(ref['pg_id'], []).append(i)
        if ref['ts_id']: ts_idx_d.setdefault(ref['ts_id'], []).append(i)
        if ref['icd9_id']: icd9_idx_d.setdefault(ref['icd9_id'], []).append(i)

    data['shanghai_new'] = sh_new
    data['cross_refs'] = cross_refs
    data['_index'] = {'sh': sh_idx_d, 'pg': pg_idx_d, 'ts': ts_idx_d, 'icd9': icd9_idx_d}
    data['stats'] = {
        'shanghai_count': len(sh_all),
        'shanghai_new_count': len(sh_new),
        'pricing_guide_count': len(pg_all),
        'tech_specs_count': len(ts_all),
        'icd9_count': len(data['icd9']),
        'cross_refs_count': len(cross_refs),
        'shanghai_matched': sum(1 for r in cross_refs if r['pg_id']),
        'full_chain': sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id']),
    }

    # Save
    with open(os.path.join(BASE, 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    with gzip.open(os.path.join(BASE, 'data.json.gz'), 'wb', compresslevel=6) as f:
        f.write(jbytes)

    print(f'\n=== Results ===')
    print(f'  New SH rehab items: {added_sh}')
    print(f'  New cross-refs: {new_refs}')
    print(f'  Updated refs: {updated_refs}')
    print(f'  Total cross-refs: {len(cross_refs)}')
    print(f'  SH matched: {data["stats"]["shanghai_matched"]}')
    print(f'  Full chain: {data["stats"]["full_chain"]}')

if __name__ == '__main__':
    main()
