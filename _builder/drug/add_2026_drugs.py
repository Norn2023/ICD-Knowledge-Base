"""
Add drugs found in 2026医保分类 but NOT in 2025 catalog to drugs.json.
Tags them as _source='2026医保分类' for easy identification.
"""
import json, sys, os, gzip

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 60)
    print("添加 2026医保分类 新药品到目录")
    print("=" * 60)

    # Load current drugs
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    orig_count = len(drugs)

    # Load new drugs
    with open(os.path.join(BASE, 'new_drugs_2026_final.json'), 'r', encoding='utf-8') as f:
        new_drugs = json.load(f)

    print(f"当前目录: {orig_count} drugs")
    print(f"待添加: {len(new_drugs)} drugs")

    # Build set of existing names for dedup
    import re
    def norm(s):
        return re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+', '', str(s))

    existing = set()
    for d in drugs:
        existing.add(norm(d.get('name', '')))

    added = 0
    skipped = 0
    for item in new_drugs:
        name = item['name'].strip()
        if not name:
            skipped += 1
            continue
        n = norm(name)
        if n in existing:
            skipped += 1
            continue

        # Infer type from name patterns
        dtype = '西药'
        # Chinese medicine patterns
        zm_patterns = ['丸','散','膏','丹','颗粒','糖浆','合剂','口服液','片','胶囊','注射液']
        # Most are 西药 by default; could check first char

        # Create minimal drug entry
        entry = {
            'name': name,
            'type': dtype,
            'level': '',
            'code': '',
            'cat': '',
            'form': '',
            'note': '',
            'variants': [],
            '_source': '2026医保分类',
            '_has_variants': False,
            '_in_rx': False,
            '_product_count_2026': item['products']
        }
        drugs.append(entry)
        existing.add(n)
        added += 1

    print(f"\n实际添加: {added}")
    print(f"跳过重复: {skipped}")
    print(f"新总数: {len(drugs)}")

    # Save
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print(f"\n✅ Saved drugs.json ({len(drugs)} drugs)")
    print(f"   新增: {added} 个 (来自2026医保分类)")

if __name__ == '__main__':
    main()
