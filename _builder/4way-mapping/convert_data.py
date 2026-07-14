"""
Convert 四方映射表.xlsx to structured JSON for web display.
Creates 4 index tables + cross-reference lookup.
"""
import json
import openpyxl
import re
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(BASE), '四方映射表.xlsx')
OUT = os.path.join(BASE, 'data.json')

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
ws = wb['四方映射']

shanghai_items = []      # 上海价格项目
pricing_guide_items = [] # 立项指南项目
tech_spec_items = []     # 技术规范项目
icd9_items = []          # ICD-9项目
cross_refs = []          # 跨表链接

# Track unique items with IDs
sh_by_code = {}
pg_by_seq = {}
ts_by_code = {}
icd9_by_code = {}

item_id = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    sh_code = str(row[0]).strip() if row[0] else ''
    sh_name = str(row[1]).strip() if row[1] else ''
    sh_desc = str(row[2]).strip()[:300] if row[2] else ''
    sh_unit = str(row[3]).strip() if row[3] else ''
    sh_price = str(row[4]).strip() if row[4] else ''
    sh_notes = str(row[5]).strip() if row[5] else ''
    sh_pg_score = str(row[6]).strip() if row[6] else ''
    pg_ts_score = str(row[7]).strip() if row[7] else ''
    pg_seq = str(row[8]).strip() if row[8] else ''
    pg_category = str(row[9]).strip() if row[9] else ''
    pg_name = str(row[10]).strip() if row[10] else ''
    pg_output = str(row[11]).strip()[:200] if row[11] else ''
    pg_cost = str(row[12]).strip()[:200] if row[12] else ''
    pg_unit = str(row[13]).strip() if row[13] else ''
    ts_code = str(row[14]).strip() if row[14] else ''
    ts_name = str(row[15]).strip() if row[15] else ''
    ts_desc = str(row[16]).strip()[:200] if row[16] else ''
    icd9_yb_code = str(row[17]).strip() if row[17] else ''
    icd9_yb_name = str(row[18]).strip() if row[18] else ''
    icd9_gl_code = str(row[19]).strip() if row[19] else ''
    icd9_gl_name = str(row[20]).strip() if row[20] else ''

    # Shanghai item
    if sh_code and sh_code not in sh_by_code:
        sh_id = f"sh_{len(shanghai_items)}"
        sh_item = {
            'id': sh_id,
            'code': sh_code,
            'name': sh_name,
            'desc': sh_desc,
            'unit': sh_unit,
            'price': sh_price,
            'notes': sh_notes,
        }
        shanghai_items.append(sh_item)
        sh_by_code[sh_code] = sh_id

    # Pricing guide item
    if pg_seq and pg_seq not in pg_by_seq:
        pg_id = f"pg_{len(pricing_guide_items)}"
        pg_item = {
            'id': pg_id,
            'seq': pg_seq,
            'category': pg_category,
            'name': pg_name,
            'output': pg_output,
            'cost_structure': pg_cost,
            'unit': pg_unit,
        }
        pricing_guide_items.append(pg_item)
        pg_by_seq[pg_seq] = pg_id

    # Tech spec item
    if ts_code and ts_code not in ts_by_code:
        ts_id = f"ts_{len(tech_spec_items)}"
        ts_item = {
            'id': ts_id,
            'code': ts_code,
            'name': ts_name,
            'desc': ts_desc,
        }
        tech_spec_items.append(ts_item)
        ts_by_code[ts_code] = ts_id

    # ICD-9 item
    if icd9_yb_code and icd9_yb_code not in icd9_by_code:
        icd9_id = f"icd9_{len(icd9_items)}"
        icd9_item = {
            'id': icd9_id,
            'yb_code': icd9_yb_code,
            'yb_name': icd9_yb_name,
            'gl_code': icd9_gl_code,
            'gl_name': icd9_gl_name,
        }
        icd9_items.append(icd9_item)
        icd9_by_code[icd9_yb_code] = icd9_id

    # Cross-reference (always create, so we have all relationships)
    ref = {
        'sh_id': sh_by_code.get(sh_code, ''),
        'sh_name': sh_name,
        'sh_code': sh_code,
        'pg_id': pg_by_seq.get(pg_seq, ''),
        'pg_name': pg_name,
        'pg_seq': pg_seq,
        'pg_category': pg_category,
        'ts_id': ts_by_code.get(ts_code, ''),
        'ts_name': ts_name,
        'ts_code': ts_code,
        'icd9_id': icd9_by_code.get(icd9_yb_code, ''),
        'icd9_name': icd9_yb_name,
        'icd9_code': icd9_yb_code,
        'sh_pg_score': sh_pg_score,
        'pg_ts_score': pg_ts_score,
    }
    cross_refs.append(ref)

wb.close()

# Build reverse index for fast lookup
# For each item ID, find all cross-ref rows
sh_index = {}
pg_index = {}
ts_index = {}
icd9_index = {}

for i, ref in enumerate(cross_refs):
    sid = ref['sh_id']
    pid = ref['pg_id']
    tid = ref['ts_id']
    iid = ref['icd9_id']

    if sid:
        if sid not in sh_index:
            sh_index[sid] = []
        sh_index[sid].append(i)
    if pid:
        if pid not in pg_index:
            pg_index[pid] = []
        pg_index[pid].append(i)
    if tid:
        if tid not in ts_index:
            ts_index[tid] = []
        ts_index[tid].append(i)
    if iid:
        if iid not in icd9_index:
            icd9_index[iid] = []
        icd9_index[iid].append(i)

data = {
    'shanghai': shanghai_items,
    'pricing_guide': pricing_guide_items,
    'tech_specs': tech_spec_items,
    'icd9': icd9_items,
    'cross_refs': cross_refs,
    '_index': {
        'sh': {k: v for k, v in sh_index.items()},
        'pg': {k: v for k, v in pg_index.items()},
        'ts': {k: v for k, v in ts_index.items()},
        'icd9': {k: v for k, v in icd9_index.items()},
    },
    'stats': {
        'shanghai_count': len(shanghai_items),
        'pricing_guide_count': len(pricing_guide_items),
        'tech_specs_count': len(tech_spec_items),
        'icd9_count': len(icd9_items),
        'cross_refs_count': len(cross_refs),
        'shanghai_matched': sum(1 for r in cross_refs if r['pg_id']),
        'full_chain': sum(1 for r in cross_refs if r['sh_id'] and r['pg_id'] and r['ts_id'] and r['icd9_id']),
    }
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Generated: {OUT}")
print(f"  Shanghai items: {len(shanghai_items)}")
print(f"  Pricing guide items: {len(pricing_guide_items)}")
print(f"  Tech specs items: {len(tech_spec_items)}")
print(f"  ICD-9 items: {len(icd9_items)}")
print(f"  Cross-refs: {len(cross_refs)}")
print(f"  Full chain: {data['stats']['full_chain']}")

# Also create gzip version for faster serving
import gzip
json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
gz_path = OUT + '.gz'
with gzip.open(gz_path, 'wb', compresslevel=6) as f:
    f.write(json_bytes)
print(f"  Gzipped: {gz_path} ({len(json_bytes)} -> {os.path.getsize(gz_path)} bytes)")
