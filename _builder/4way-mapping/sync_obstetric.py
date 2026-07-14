"""
Sync obstetric mapping to the 4-way mapping data.
"""
import json
import gzip
import os
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, 'data.json')

def load_json():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    # Also gzip
    json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    with gzip.open(DATA_FILE + '.gz', 'wb', compresslevel=6) as f:
        f.write(json_bytes)
    print(f'Saved: {DATA_FILE} ({len(json_bytes)} bytes)')

def clean(s):
    return s.replace('\n','').replace(' ','').replace('（','(').replace('）',')').strip()

def fuzzy_match(target, candidates, key='name', threshold=0.55):
    """Find best match for target in candidates list."""
    ct = clean(target)
    best_score = 0
    best_idx = -1
    for i, c in enumerate(candidates):
        cn = clean(c.get(key, ''))
        if not cn:
            continue
        # Exact match
        if ct == cn:
            return i, 1.0
        # Contains
        if ct in cn or cn in ct:
            return i, 0.9
        # Fuzzy
        score = SequenceMatcher(None, ct, cn).ratio()
        if score > best_score:
            best_score = score
            best_idx = i
    if best_score >= threshold:
        return best_idx, best_score
    return -1, 0

def main():
    # Load obstetric mappings
    with open(os.path.join(os.path.dirname(os.path.dirname(BASE)), '_obstetric_mappings.json'), 'r', encoding='utf-8') as f:
        obstetric = json.load(f)

    # Load current mapping data
    data = load_json()

    sh_items = data['shanghai']
    pg_items = data['pricing_guide']
    ts_items = data['tech_specs']
    cross_refs = data['cross_refs']

    new_refs = 0
    updated_refs = 0

    for ob in obstetric:
        pg_name = ob['pg_name']
        sh_names = ob['sh_names']
        ts_names = ob['ts_names']

        # Find pricing guide item
        pg_idx, pg_score = fuzzy_match(pg_name, pg_items, 'name', threshold=0.6)
        pg_id = pg_items[pg_idx]['id'] if pg_idx >= 0 else ''
        pg_seq = pg_items[pg_idx]['seq'] if pg_idx >= 0 else ''

        if pg_idx < 0:
            print(f'  [SKIP] PG not found: {pg_name}')
            continue

        print(f'[OK] {pg_name} -> PG:{pg_id} (score={pg_score:.2f})')

        # For each Shanghai price name in this mapping
        for sh_name in sh_names:
            sh_idx, sh_score = fuzzy_match(sh_name, sh_items, 'name', threshold=0.55)

            # Find tech spec names
            ts_ids = []
            for ts_name in ts_names:
                ts_idx, ts_score = fuzzy_match(ts_name, ts_items, 'name', threshold=0.55)
                if ts_idx >= 0:
                    ts_ids.append({
                        'id': ts_items[ts_idx]['id'],
                        'code': ts_items[ts_idx]['code'],
                        'name': ts_items[ts_idx]['name'],
                        'score': ts_score,
                    })

            if sh_idx >= 0:
                sh_id = sh_items[sh_idx]['id']
                sh_code = sh_items[sh_idx]['code']

                # Check if cross-ref already exists
                existing = None
                for i, ref in enumerate(cross_refs):
                    if ref['sh_id'] == sh_id and ref['pg_id'] == pg_id:
                        existing = i
                        break

                ts_score_str = f'{ts_ids[0]["score"]:.2f}' if ts_ids else ''
                ref = {
                    'sh_id': sh_id,
                    'sh_name': sh_items[sh_idx]['name'],
                    'sh_code': sh_code,
                    'pg_id': pg_id,
                    'pg_name': pg_name,
                    'pg_seq': pg_seq,
                    'pg_category': pg_items[pg_idx]['category'],
                    'ts_id': ts_ids[0]['id'] if ts_ids else '',
                    'ts_name': ts_ids[0]['name'] if ts_ids else '',
                    'ts_code': ts_ids[0]['code'] if ts_ids else '',
                    'icd9_id': '',
                    'icd9_name': '',
                    'icd9_code': '',
                    'sh_pg_score': f'{max(sh_score, 0.85):.2f}',
                    'pg_ts_score': ts_score_str,
                }

                if existing is not None:
                    cross_refs[existing].update(ref)
                    updated_refs += 1
                else:
                    cross_refs.append(ref)
                    new_refs += 1

                print(f'    SH: {sh_name} -> {sh_id} (score={sh_score:.2f})')
                if ts_ids:
                    print(f'    TS: {ts_ids[0]["name"]} -> {ts_ids[0]["id"]} (score={ts_ids[0]["score"]:.2f})')

    # Update index
    sh_index = {}
    pg_index = {}
    ts_index = {}
    icd9_index = {}
    for i, ref in enumerate(cross_refs):
        if ref['sh_id']: sh_index.setdefault(ref['sh_id'], []).append(i)
        if ref['pg_id']: pg_index.setdefault(ref['pg_id'], []).append(i)
        if ref['ts_id']: ts_index.setdefault(ref['ts_id'], []).append(i)
        if ref['icd9_id']: icd9_index.setdefault(ref['icd9_id'], []).append(i)

    data['_index'] = {
        'sh': sh_index,
        'pg': pg_index,
        'ts': ts_index,
        'icd9': icd9_index,
    }
    data['cross_refs'] = cross_refs
    data['stats'] = {
        'shanghai_count': len(sh_items),
        'pricing_guide_count': len(pg_items),
        'tech_specs_count': len(ts_items),
        'icd9_count': len(data['icd9']),
        'cross_refs_count': len(cross_refs),
        'shanghai_matched': sum(1 for r in cross_refs if r['pg_id']),
        'full_chain': sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id']),
    }

    stats = data['stats']
    print(f'\nResults:')
    print(f'  New refs: {new_refs}')
    print(f'  Updated refs: {updated_refs}')
    print(f'  Total cross-refs: {len(cross_refs)}')
    print(f'  Shanghai matched: {stats["shanghai_matched"]}')
    print(f'  Full chain: {stats["full_chain"]}')

    save_json(data)

if __name__ == '__main__':
    main()
