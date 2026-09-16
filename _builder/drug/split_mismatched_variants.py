"""
Split drug variants where the registered name indicates a DIFFERENT active ingredient
or formulation than the parent drug. Reassign to correct parent or create new entries.

Examples:
- 艾司奥美拉唑 variants under 奥美拉唑 → move to 埃索美拉唑
- 奥美拉唑钠 variants under 奥美拉唑 → separate drug
- Compound 碳酸氢钠 products → separate from plain 碳酸氢钠
- Corrupted double-name variants → split and duplicate
"""
import json, sys, os, gzip, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    if not s: return ''
    return re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ\-\+\.\,/]+', '', str(s))

def extract_core_name(name):
    """Extract the core drug name (active ingredient) from a product name."""
    # Remove common prefixes/suffixes
    name = re.sub(r'(注射用|注射液|片|胶囊|颗粒|口服|溶液|混悬|滴眼|滴耳|喷雾|吸入|软膏|乳膏|凝胶|栓|搽剂|洗剂|贴剂|糖浆|散|丸|冲剂|粉针|肠溶|缓释|控释|分散|咀嚼|泡腾|口崩|含片|阴道)', '', name)
    return name.strip()

def main():
    print("=" * 60)
    print("拆分产品明细 — 不同注册名称分离")
    print("=" * 60)

    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    # Build lookup: normalized core name → list of drug entries
    # This helps find the correct parent for misplaced variants
    drug_index = {}  # norm_core → drug
    for d in drugs:
        nc = norm(extract_core_name(d.get('name', '')))
        if nc and len(nc) >= 3:
            if nc not in drug_index:
                drug_index[nc] = []
            drug_index[nc].append(d)

    # Rules for splitting: (parent_drug_name_pattern, wrong_reg_pattern, correct_drug_name)
    # If a variant's reg_name matches wrong_reg_pattern, move it to correct_drug_name
    SPLIT_RULES = [
        # Esomeprazole (艾司奥美拉唑/埃索美拉唑) should not be under 奥美拉唑
        ('奥美拉唑', r'艾司奥美拉唑|埃索美拉唑', '埃索美拉唑(艾司奥美拉唑)'),
        # Omeprazole sodium should be separate from omeprazole
        ('奥美拉唑', r'奥美拉唑钠(?!.*碳酸氢钠)', '奥美拉唑钠'),
        # Omeprazole magnesium should be separate
        ('奥美拉唑', r'奥美拉唑镁(?!.*碳酸氢钠)', '奥美拉唑镁'),
        # Compound bicarb products should not be under plain 碳酸氢钠
        ('碳酸氢钠', r'复方.*碳酸氢钠|铋镁.*碳酸氢钠|龙胆.*碳酸氢钠|大黄.*碳酸氢钠|颠茄.*碳酸氢钠', None),  # None = create individual drugs
        # Amoxicillin/clavulanate should not be under amoxicillin
        ('阿莫西林', r'克拉维酸', '阿莫西林克拉维酸'),
        # Piperacillin/tazobactam vs piperacillin
        ('哌拉西林', r'他唑巴坦|舒巴坦', '哌拉西林钠他唑巴坦钠'),
        # Lansoprazole variants
        ('兰索拉唑', r'右兰索拉唑', '注射用右兰索拉唑'),
        # Ilaprazole sodium vs ilaprazole
        ('艾普拉唑', r'艾普拉唑钠(?!.*奥美拉唑)', '注射用艾普拉唑钠'),
    ]

    total_moved = 0
    total_created = 0
    compound_creates = 0

    for d in drugs:
        parent_name = d.get('name', '')
        variants = d.get('variants', [])
        if not variants:
            continue

        # Check each split rule
        for pattern, wrong_re, target_name in SPLIT_RULES:
            if pattern not in parent_name:
                continue

            wrong_regex = re.compile(wrong_re)
            keep = []
            move_out = []

            for v in variants:
                rn = str(v.get('reg_name', ''))
                if wrong_regex.search(rn):
                    move_out.append(v)
                else:
                    keep.append(v)

            if not move_out:
                continue

            # Find or create target drug
            target_drug = None
            if target_name:
                target_norm = norm(extract_core_name(target_name))
                # Try exact name match first
                for dd in drugs:
                    if dd.get('name', '') == target_name:
                        target_drug = dd
                        break
                # Try core name match
                if not target_drug and target_norm in drug_index:
                    target_drug = drug_index[target_norm][0]

            if target_drug:
                # Move variants to existing target
                target_drug.setdefault('variants', []).extend(move_out)
                print(f"  {parent_name} → {target_drug['name']}: 移动 {len(move_out)} 个产品")
                total_moved += len(move_out)
            elif target_name:
                # Create new drug entry
                new_drug = {
                    'name': target_name,
                    'type': d.get('type', '西药'),
                    'level': d.get('level', ''),
                    'code': d.get('code', ''),
                    'cat': d.get('cat', ''),
                    'subcat': d.get('subcat', ''),
                    'form': '',
                    'note': '',
                    'variants': move_out,
                    '_source': '拆分自' + parent_name,
                    '_has_variants': True,
                }
                drugs.append(new_drug)
                nc = norm(extract_core_name(target_name))
                if nc not in drug_index:
                    drug_index[nc] = []
                drug_index[nc].append(new_drug)
                print(f"  {parent_name} → 新建「{target_name}」: {len(move_out)} 个产品")
                total_created += 1
                total_moved += len(move_out)
            else:
                # target_name is None: create individual drugs from compound names
                # Group variants by their compound name prefix
                groups = defaultdict(list)
                for v in move_out:
                    rn = str(v.get('reg_name', ''))
                    # Extract compound name (first 4-6 chars typically identify the compound)
                    key = rn[:8] if len(rn) >= 8 else rn
                    groups[key].append(v)

                for grp_key, grp_vars in groups.items():
                    # Use first variant's reg_name as the new drug name
                    new_name = grp_vars[0].get('reg_name', grp_key)
                    # Clean: remove dosage form suffixes
                    for sfx in ['片', '胶囊', '颗粒', '散', '溶液', '注射液']:
                        new_name = re.sub(sfx + '$', '', new_name)
                    nd = {
                        'name': new_name,
                        'type': d.get('type', '西药'),
                        'level': '',
                        'code': '',
                        'cat': d.get('cat', ''),
                        'form': '',
                        'note': '',
                        'variants': grp_vars,
                        '_source': '拆自' + parent_name,
                        '_has_variants': True,
                    }
                    drugs.append(nd)
                    compound_creates += 1
                    print(f"  {parent_name} → 新建「{new_name}」: {len(grp_vars)} 个产品")
                total_moved += len(move_out)

            d['variants'] = keep

    # Step 2: Clean corrupted variant names (names containing multiple drug names)
    # These are PDF artifacts where two rows merged
    corrupted_fixed = 0
    for d in drugs:
        for v in d.get('variants', []):
            rn = str(v.get('reg_name', ''))
            # Detect double-drug names (e.g., "注射用艾普拉唑钠奥美拉唑钠肠溶片")
            # Pattern: two drug names concatenated without separator
            double_patterns = [
                (r'(注射用\S+?钠)(奥美拉唑\S+)', r'\1'),  # first drug is the real one
                (r'(注射用\S+?钠)(肠溶\S+)', r'\1'),
                (r'(缩合葡萄糖\S+)(碳酸氢钠\S+)', r'\1'),
                (r'(龙胆碳酸氢钠片)(碳酸氢钠片)', r'\1'),
            ]
            for pat, repl in double_patterns:
                if re.search(pat, rn):
                    new_rn = re.sub(pat, repl, rn)
                    if new_rn != rn:
                        v['reg_name'] = new_rn
                        corrupted_fixed += 1
                        break

    print(f"\n清理损坏品名: {corrupted_fixed} 条")

    # Stats
    total_variants = sum(len(d.get('variants', [])) for d in drugs)
    print(f"\n总计: {len(drugs)} drugs, {total_variants} variants")
    print(f"移动产品: {total_moved}, 新建药品: {total_created + compound_creates}")
    print(f"修复损坏品名: {corrupted_fixed}")

    # Save
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print(f"\n✅ Saved")

if __name__ == '__main__':
    main()
