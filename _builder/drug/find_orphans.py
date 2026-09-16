"""
Find orphan variants: product details whose names don't match any drug in the 2025 catalog.
Also: find drugs in 2025 catalog without variants.
"""
import json, sys, os, re, gzip
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    if not s: return ''
    return re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+', '', str(s))

def main():
    print("=" * 60)
    print("2025医保目录 × 产品明细 交叉比对")
    print("=" * 60)

    # Load drugs
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    # Build lookup: normalized drug names → drug
    drug_by_norm = {}
    for d in drugs:
        n = norm(d.get('name', ''))
        if n and len(n) >= 3:
            drug_by_norm[n] = d

    # Fast: collect all normalized drug names + variant names into a set
    all_catalog_names = set(drug_by_norm.keys())
    # Also add all variant reg_names from drugs that already have variants
    for d in drugs:
        for v in d.get('variants', []):
            rn = norm(str(v.get('reg_name', '')))
            if rn and len(rn) >= 3:
                all_catalog_names.add(rn)

    # Find orphan variants: those whose reg_name is completely absent from the catalog name set
    orphan_variants = []
    matched_variants = 0
    no_variant_drugs = []

    for d in drugs:
        variants = d.get('variants', [])
        if not variants:
            no_variant_drugs.append(d['name'])
            continue
        dname_norm = norm(d.get('name', ''))
        for v in variants:
            rn = norm(str(v.get('reg_name', '')))
            tn = norm(str(v.get('trade_name', '')))
            # A variant is "matched" if its name or trade name is in the catalog set
            # OR if a catalog drug name is a substring of the variant name or vice versa
            matched = (rn in all_catalog_names) or (tn and tn in all_catalog_names)
            if not matched and rn and dname_norm:
                # Try substring matching only as fallback
                matched = (dname_norm in rn) or (rn in dname_norm)
            if matched:
                matched_variants += 1
            else:
                orphan_variants.append((d['name'], v.get('reg_name', ''), v.get('trade_name', ''), v.get('code', '')))

    print(f"\n2025目录: {len(drugs)} drugs")
    print(f"无产品明细: {len(no_variant_drugs)} drugs")
    total_v = matched_variants + len(orphan_variants)
    print(f"产品明细总量: {total_v}")
    print(f"已匹配: {matched_variants}")
    print(f"孤立产品: {len(orphan_variants)} ({100*len(orphan_variants)/max(1,total_v):.1f}%)")

    if orphan_variants:
        by_drug = Counter(o[0] for o in orphan_variants)
        print(f"\n孤立产品最多的药品 (前20):")
        for name, cnt in by_drug.most_common(20):
            samples = list(set(o[1] for o in orphan_variants if o[0] == name))[:3]
            print(f"  {name}: {cnt}个, 注册名: {samples}")

    print(f"\n2025目录中无产品明细的药品 (前30):")
    for name in no_variant_drugs[:30]:
        print(f"  🟡 {name}")
    print(f"  ... 共 {len(no_variant_drugs)} 个")

if __name__ == '__main__':
    main()
