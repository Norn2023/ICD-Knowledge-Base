"""
Smart match audit rules to drugs: exact → base name → substring.
Compound names like 奥美拉唑碳酸氢钠干混悬剂 → match to 奥美拉唑.
"""
import json, sys, os, gzip, re

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    if not s: return ''
    return re.sub(r'[\s　（）()ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ\-]+', '', str(s)).lower()

def extract_base_name(name):
    """Extract the base drug name by stripping suffixes/modifiers/forms."""
    # Remove dosage form suffixes
    for sfx in ['干混悬剂', '注射液', '注射用', '注射剂', '缓释片', '缓释胶囊',
                '控释片', '肠溶片', '肠溶胶囊', '分散片', '咀嚼片', '口崩片',
                '泡腾片', '滴眼液', '滴耳液', '滴鼻液', '喷雾剂', '气雾剂',
                '软膏', '乳膏', '凝胶', '栓剂', '栓', '贴剂', '贴膏','洗剂',
                '搽剂', '含片', '颗粒', '糖浆', '口服液', '混悬液', '混悬剂',
                '胶囊', '片', '丸', '散', '膜', '吸入剂', '粉雾剂',
                '舌下片', '含漱液', '溶液', '酊剂', '擦剂', '灌肠剂',
                '阴道片', '阴道栓', '植入剂', '冲洗剂']:
        if name.endswith(sfx):
            return name[:-len(sfx)]
    # Remove dosage specifiers like (Ⅰ), (Ⅱ), (III), c6~24, 18aa, etc.
    name = re.sub(r'[（(][ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ\da-z~～]+[）)]$', '', name)
    name = re.sub(r'\d+[a-z]{2}$', '', name)
    name = re.sub(r'c\d+[～~]\d+$', '', name)
    return name.strip()

def get_progressive_keys(name):
    """Generate progressively shorter keys for matching: base name → shorter stems."""
    n = norm(name)
    keys = [n]  # exact first
    base = extract_base_name(n)
    if base and base != n:
        keys.append(base)
    # Also try removing common modifiers from the end
    modifiers = ['钠', '钾', '钙', '镁', '锌', '铁', '盐酸', '硫酸', '磷酸',
                 '葡萄糖', '氯化钠', '碳酸氢钠', '枸橼酸', '酒石酸', '马来酸',
                 '苯磺酸', '甲磺酸', '琥珀酸', '醋酸', '乳糖酸', '门冬氨酸',
                 '谷氨酸', '精氨酸', '赖氨酸', '复合', '复方']
    for mod in sorted(modifiers, key=len, reverse=True):
        if base.endswith(mod) and len(base) - len(mod) >= 3:
            shorter = base[:-len(mod)]
            if shorter not in keys:
                keys.append(shorter)
    return keys

def main():
    print("=" * 60)
    print("智能匹配审核规则 → 药品")
    print("=" * 60)

    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    with open(os.path.join(BASE, 'audit_rules.json'), 'r', encoding='utf-8') as f:
        rules = json.load(f)
    print(f"药品: {len(drugs)}, 规则: {len(rules)}")

    # Index rules by drug name
    rules_by_name = {}
    for r in rules:
        rn = r.get('drug_name', '').strip()
        if rn:
            rnn = norm(rn)
            if rnn not in rules_by_name:
                rules_by_name[rnn] = []
            rules_by_name[rnn].append(r)

    # Build drug lookup: normalized → drug object
    drug_by_norm = {}
    drug_by_base = {}
    for d in drugs:
        d['rules'] = []
        dn = d.get('name', '')
        dnn = norm(dn)
        if dnn and len(dnn) >= 3:
            drug_by_norm[dnn] = d
            base = extract_base_name(dnn)
            if base and base != dnn:
                if base not in drug_by_base:
                    drug_by_base[base] = []
                drug_by_base[base].append(d)

    matched_drugs = 0
    unmatched_rules = {}

    # For each rule, find ALL matching drugs (may match multiple)
    for rnn, rlist in rules_by_name.items():
        matched_any = False
        rule_keys = get_progressive_keys(rnn)
        matched_drug_set = set()  # avoid duplicate assignment

        # Try each progressive key — match to ALL applicable drugs, not just first
        for key in rule_keys:
            if len(key) < 3:
                continue
            # Exact match
            if key in drug_by_norm:
                d = drug_by_norm[key]
                if id(d) not in matched_drug_set:
                    for r in rlist:
                        if r not in d['rules']:
                            d['rules'].append(r)
                    matched_drug_set.add(id(d))
                    matched_any = True
            # Base name match
            if key in drug_by_base:
                for d in drug_by_base[key]:
                    if id(d) not in matched_drug_set:
                        for r in rlist:
                            if r not in d['rules']:
                                d['rules'].append(r)
                        matched_drug_set.add(id(d))
                        matched_any = True

        # Substring fallback
        if not matched_any:
            for dnn, d in drug_by_norm.items():
                if len(dnn) >= 4 and len(rnn) >= 4:
                    if dnn in rnn or rnn in dnn:
                        if id(d) not in matched_drug_set:
                            for r in rlist:
                                if r not in d['rules']:
                                    d['rules'].append(r)
                            matched_drug_set.add(id(d))
                            matched_any = True

        if matched_any:
            matched_drugs += len(matched_drug_set)
        else:
            unmatched_rules[rnn] = len(rlist)

    total_rules = sum(len(d.get('rules', [])) for d in drugs)
    drugs_with_rules = sum(1 for d in drugs if d.get('rules'))

    print(f"\n匹配完成:")
    print(f"  药品有规则: {drugs_with_rules}")
    print(f"  规则已匹配: {total_rules}/{len(rules)}")
    print(f"  未匹配规则组: {len(unmatched_rules)}")

    # Show unmatched
    print(f"\n未匹配规则 (前20):")
    for name, cnt in sorted(unmatched_rules.items(), key=lambda x: -x[1])[:20]:
        print(f"  {name}: {cnt} rules")

    # Verify specific cases
    print(f"\n验证:")
    for d in drugs:
        if d.get('name') == '奥美拉唑':
            print(f"  奥美拉唑: {len(d.get('rules',[]))} rules")
            for r in d.get('rules', [])[:5]:
                print(f"    - {r.get('drug_name','?')}: {str(r.get('check_logic',''))[:60]}")

    # Save
    out = os.path.join(BASE, 'drugs.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(out, 'rb') as fin:
        with gzip.open(out + '.gz', 'wb', compresslevel=9) as fout:
            fout.write(fin.read())

    print(f"\n✅ Saved")

if __name__ == '__main__':
    main()
