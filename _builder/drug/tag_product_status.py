"""
Tag drugs: with/without product variants, 处方集收录标记.
"""
import json, sys, os, gzip

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 50)
    print("药品产品明细状态标注")
    print("=" * 50)

    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    print(f"2025目录: {len(drugs)} drugs")

    with open(os.path.join(BASE, 'clinical_ref_index.json'), 'r', encoding='utf-8') as f:
        clin = json.load(f)
    rx_set = set(e['name'] for e in clin.get('rx', []))
    print(f"处方集: {len(rx_set)} drugs")

    no_v = 0; rx_no_v = 0; has_v = 0
    for d in drugs:
        d['_has_variants'] = bool(d.get('variants'))
        d['_in_rx'] = d.get('name', '') in rx_set
        if d['_has_variants']:
            has_v += 1
        else:
            no_v += 1
            if d['_in_rx']:
                rx_no_v += 1

    print(f"有产品: {has_v}, 无产品: {no_v}, 处方集无产品: {rx_no_v}")

    with open(os.path.join(BASE, 'drugs.json'), 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, 'drugs.json'), 'rb') as fi:
        with gzip.open(os.path.join(BASE, 'drugs.json.gz'), 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print(f"\n处方集收录但无产品明细 (前40):")
    count = 0
    for d in drugs:
        if d['_in_rx'] and not d['_has_variants']:
            print(f"  🔴 {d['name']}")
            count += 1
            if count >= 40: break

    print(f"\n✅ Done. 无产品: {no_v}, 处方集缺产品: {rx_no_v}")

if __name__ == '__main__':
    main()
