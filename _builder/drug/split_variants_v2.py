"""
Clean v2: Split mismatched drug variants — process ALL drugs first,
collect moves, then apply in one pass. No infinite loop possible.
"""
import json, sys, os, gzip, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 60)
    print("产品明细拆分 — v2 (安全版)")
    print("=" * 60)

    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    # --- Step 1: Analyze all drugs, collect what needs to move ---
    # moves: [(from_drug_idx, variant_indices_to_remove, target_name, moved_variants)]
    moves = []

    for di, d in enumerate(drugs):
        parent = d.get('name', '')
        variants = d.get('variants', [])
        if not variants:
            continue

        to_remove = set()

        # Rule: 艾司奥美拉唑/埃索美拉唑 should NOT be under 奥美拉唑
        if '奥美拉唑' in parent and '艾司' not in parent and '埃索' not in parent and '碳酸氢钠' not in parent:
            eso_vars = []
            for vi, v in enumerate(variants):
                rn = str(v.get('reg_name', ''))
                if re.search(r'艾司奥美拉唑|埃索美拉唑', rn):
                    eso_vars.append(v)
                    to_remove.add(vi)
            if eso_vars:
                moves.append((di, to_remove.copy(), '埃索美拉唑(艾司奥美拉唑)', eso_vars, '奥美拉唑→艾司奥美拉唑'))

        # Rule: 碳酸氢钠 compounds should be separate
        if parent == '碳酸氢钠':
            compound_groups = defaultdict(list)
            plain = []
            for vi, v in enumerate(variants):
                rn = str(v.get('reg_name', ''))
                if any(kw in rn for kw in ['复方', '铋镁', '龙胆', '大黄', '颠茄', '小儿']):
                    # Extract compound identifier
                    key = rn[:6]
                    compound_groups[key].append((vi, v))
                else:
                    plain.append(v)

            if compound_groups:
                for key, group_vars in compound_groups.items():
                    name = group_vars[0][1].get('reg_name', key)
                    # Truncate to a reasonable drug name
                    for sfx in ['片', '胶囊', '颗粒', '散']:
                        name = re.sub(sfx + r'\s*$', '', name)
                    name = name[:20]  # keep short
                    var_list = [v for _, v in group_vars]
                    remove_indices = {vi for vi, _ in group_vars}
                    moves.append((di, remove_indices, name, var_list, '碳酸氢钠→复方'))

        # Rule: 阿莫西林克拉维酸 should not be under 阿莫西林
        if parent == '阿莫西林':
            clav_vars = []
            for vi, v in enumerate(variants):
                rn = str(v.get('reg_name', ''))
                if '克拉维酸' in rn:
                    clav_vars.append(v)
                    to_remove.add(vi)
            if clav_vars:
                moves.append((di, to_remove.copy(), '阿莫西林克拉维酸', clav_vars, '阿莫西林→克拉维酸'))

        # Rule: 艾普拉唑/泮托拉唑/兰索拉唑 variants should NOT be under 奥美拉唑
        if '奥美拉唑' in parent and '艾司' not in parent and '埃索' not in parent and '碳酸氢钠' not in parent:
            other_prazole = []
            for vi, v in enumerate(variants):
                rn = str(v.get('reg_name', ''))
                if re.search(r'(艾普拉唑|泮托拉唑|兰索拉唑|雷贝拉唑)', rn) and not re.search(r'奥美拉唑', rn):
                    other_prazole.append((vi, v))
            if other_prazole:
                for vi, v in other_prazole:
                    rn = str(v.get('reg_name', ''))
                    # Determine correct parent
                    if '艾普拉唑' in rn:
                        target = '注射用艾普拉唑钠'
                    elif '泮托拉唑' in rn:
                        target = '泮托拉唑'
                    elif '兰索拉唑' in rn:
                        target = '兰索拉唑'
                    elif '雷贝拉唑' in rn:
                        target = '雷贝拉唑'
                    else:
                        continue
                    to_remove.add(vi)
                    # Collect per target
                    moves.append((di, {vi}, target, [v], f'{parent}→{target}'))

        # Clean: fix corrupted double-names in variants
        for v in variants:
            rn = str(v.get('reg_name', ''))
            fixed = re.sub(r'(注射用\S+?钠)(奥美拉唑\S+)', r'\1', rn)
            fixed = re.sub(r'(龙胆碳酸氢钠片)(碳酸氢钠片)', r'\1', fixed)
            fixed = re.sub(r'(缩合葡萄糖\S+)(碳酸氢钠\S+)', r'\1', fixed)
            if fixed != rn:
                v['reg_name'] = fixed

    print(f"分析完成: {len(moves)} 个拆分操作")

    # --- Step 2: Apply moves (accumulate per drug to avoid index shift) ---
    drug_by_name = {d.get('name', ''): i for i, d in enumerate(drugs)}
    # Accumulate: per from_idx, collect all variant indices to remove + target assignments
    from_moves = defaultdict(list)  # from_idx → [(target_name, variant, reason)]
    for from_idx, remove_indices, target_name, moved_vars, reason in moves:
        for v in moved_vars:
            from_moves[from_idx].append((target_name, v, reason))

    for from_idx, assignments in from_moves.items():
        d = drugs[from_idx]
        old_vars = d.get('variants', [])
        # Group moved variants by target
        by_target = defaultdict(list)
        reasons = set()
        for target_name, v, reason in assignments:
            by_target[target_name].append(v)
            reasons.add(reason)

        # Keep only variants NOT assigned to any target (check by identity)
        moved_set = set(id(v) for v_list in by_target.values() for v in v_list)
        d['variants'] = [v for v in old_vars if id(v) not in moved_set]

        # Assign to targets
        for target_name, var_list in by_target.items():
            if target_name in drug_by_name:
                target = drugs[drug_by_name[target_name]]
                target.setdefault('variants', []).extend(var_list)
                print(f"  {'; '.join(reasons)}: → {target_name} (+{len(var_list)} variants)")
            else:
                nd = {
                    'name': target_name,
                    'type': d.get('type', '西药'),
                    'level': '',
                    'code': '',
                    'cat': d.get('cat', ''),
                    'subcat': d.get('subcat', ''),
                    'form': '',
                    'note': '',
                    'variants': var_list,
                    '_source': '拆分自' + d.get('name', ''),
                    '_has_variants': True,
                }
                drugs.append(nd)
                drug_by_name[target_name] = len(drugs) - 1
                print(f"  {'; '.join(reasons)}: → 新建「{target_name}」(+{len(var_list)} variants)")

    # Final stats
    with_v = sum(1 for d in drugs if d.get('variants'))
    total_v = sum(len(d.get('variants', [])) for d in drugs)
    print(f"\n总计: {len(drugs)} drugs, {with_v} 有产品明细, {total_v} variants")

    # Save
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print("✅ Done")

if __name__ == '__main__':
    main()
