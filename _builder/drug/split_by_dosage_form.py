"""
Split drug variants by dosage form — each drug entry should have ONE dosage form.
e.g., 碳酸氢钠片 vs 碳酸氢钠注射液 become separate entries.
"""
import json, sys, os, gzip, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm_form(fm):
    """Normalize dosage form to standard categories."""
    fm = str(fm).strip()
    if not fm: return '未知'
    # Broad categories
    if re.search(r'注射|输液|冻干|粉针', fm): return '注射剂'
    if re.search(r'片|素片|糖衣|薄膜衣|分散|咀嚼|口崩|含片|舌下|泡腾|肠溶.*片', fm): return '片剂'
    if re.search(r'胶囊|软胶囊', fm): return '胶囊剂'
    if re.search(r'颗粒|干混悬|混悬(?!液)', fm): return '颗粒剂'
    if re.search(r'口服液|口服溶|糖浆|合剂|混悬液', fm): return '口服液体剂'
    if re.search(r'软膏|乳膏|凝胶(?!.*贴)|眼膏', fm): return '外用膏剂'
    if re.search(r'滴眼|眼用', fm): return '眼用制剂'
    if re.search(r'滴耳', fm): return '滴耳剂'
    if re.search(r'滴鼻|鼻用|喷鼻', fm): return '鼻用制剂'
    if re.search(r'喷雾|气雾|吸入|粉雾', fm): return '吸入/喷雾剂'
    if re.search(r'栓', fm): return '栓剂'
    if re.search(r'贴|贴膏|贴片|凝胶贴', fm): return '贴剂'
    if re.search(r'洗剂|搽剂|涂剂|涂膜|擦剂', fm): return '外用液体剂'
    if re.search(r'散', fm): return '散剂'
    if re.search(r'丸', fm): return '丸剂'
    if re.search(r'含漱|漱口|漱液', fm): return '含漱剂'
    if re.search(r'灌肠|灌洗|冲洗', fm): return '灌洗剂'
    if re.search(r'植入', fm): return '植入剂'
    if re.search(r'膜剂|口溶膜', fm): return '膜剂'
    return fm[:10]  # truncate long unknown forms

# Reverse: normalized form → display name
FORM_DISPLAY = {
    '注射剂': '注射剂',
    '片剂': '片剂(口服)',
    '胶囊剂': '胶囊剂',
    '颗粒剂': '颗粒剂',
    '口服液体剂': '口服液体剂',
    '外用膏剂': '外用膏剂',
    '眼用制剂': '眼用制剂',
    '滴耳剂': '滴耳剂',
    '鼻用制剂': '鼻用制剂',
    '吸入/喷雾剂': '吸入/喷雾剂',
    '栓剂': '栓剂',
    '贴剂': '贴剂',
    '外用液体剂': '外用液体剂',
    '散剂': '散剂',
    '丸剂': '丸剂',
    '含漱剂': '含漱剂',
    '灌洗剂': '灌洗剂',
    '植入剂': '植入剂',
    '膜剂': '膜剂',
}

def main():
    print("=" * 60)
    print("按剂型拆分产品明细")
    print("=" * 60)

    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    new_drugs = []
    total_splits = 0

    for d in drugs:
        variants = d.get('variants', [])
        if not variants:
            continue

        # Group variants by normalized dosage form
        by_form = defaultdict(list)
        for v in variants:
            fm = norm_form(v.get('dosage_form') or v.get('form') or v.get('reg_form') or '')
            by_form[fm].append(v)

        if len(by_form) == 1:
            # Single form — update form field to normalized value
            fm = list(by_form.keys())[0]
            d['form'] = FORM_DISPLAY.get(fm, fm)
            continue

        # Multiple forms — split
        total_splits += 1
        forms = sorted(by_form.keys())
        parent_name = d.get('name', '')

        # First form stays with original drug name (update form field)
        first_form = forms[0]
        d['variants'] = by_form[first_form]
        d['form'] = FORM_DISPLAY.get(first_form, first_form)
        print(f"  {parent_name}: 保留{first_form}({len(by_form[first_form])}条)")

        # Create new entries for other forms
        for fm in forms[1:]:
            vars_list = by_form[fm]
            display_form = FORM_DISPLAY.get(fm, fm)
            # Name: "药品名（剂型）" or "药品名 剂型"
            new_name = f"{parent_name}（{display_form}）"
            nd = {
                'name': new_name,
                'type': d.get('type', '西药'),
                'level': d.get('level', ''),
                'code': d.get('code', ''),
                'cat': d.get('cat', ''),
                'subcat': d.get('subcat', ''),
                'subsubcat': d.get('subsubcat', ''),
                'form': display_form,
                'note': d.get('note', ''),
                'variants': vars_list,
                '_source': f'拆分自{parent_name}',
                '_has_variants': True,
            }
            # Copy other metadata
            for k in ['disease_type', 'essential', 'negotiated', 'nego_info', 'psychotropic_2', '_in_rx']:
                if k in d and k not in nd:
                    nd[k] = d[k]
            new_drugs.append(nd)
            print(f"    → 新建「{new_name}」({display_form}, {len(vars_list)}条)")

    drugs.extend(new_drugs)
    print(f"\n拆分药品: {total_splits}")
    print(f"新建条目: {len(new_drugs)}")
    print(f"总计: {len(drugs)} drugs")

    # Update _has_variants for all
    for d in drugs:
        d['_has_variants'] = bool(d.get('variants'))

    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print("✅ Done")

if __name__ == '__main__':
    main()
