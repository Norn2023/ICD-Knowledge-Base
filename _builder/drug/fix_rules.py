"""
Fix audit rules: shorten category names, generate logic_basis
"""
import json, sys, os, re, gzip

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

# Map long rule_type → short display name + basis template
RULE_TYPE_MAP = {
    '药品限支付疗程': ('支付疗程限制', '根据医保药品目录，该药品限定支付天数/疗程'),
    '药品区分性别使用': ('性别限制', '根据医保药品目录，该药品限定特定性别使用'),
    '药品儿童专用': ('儿童专用', '根据医保药品目录，该药品限定儿童专用'),
    '药品限儿童使用': ('儿童使用限制', '根据医保药品目录，该药品限定儿童使用'),
    '药品限医疗机构级别': ('医疗机构级别限制', '根据医保药品目录，该药品限定在特定级别医疗机构使用'),
    '药品限就医方式': ('就医方式限制', '根据医保药品目录，该药品限定特定就医方式（门诊/住院）'),
    '药品限工伤保险': ('工伤保险限制', '根据医保药品目录，该药品限定工伤保险支付'),
    '药品限生育保险': ('生育保险限制', '根据医保药品目录，该药品限定生育保险支付'),
}

def shorten_type(rt):
    """Shorten long rule type names"""
    # Handle batch-specific types like "12、12批药品限适应症-57个药633个代码（消化道和代谢）"
    m = re.match(r'(\d+)、?\d*批[药品限]*适应症', rt)
    if m:
        return f'第{m.group(1)}批药品限适应症'
    m = re.match(r'(\d+)批?药品限适应症', rt)
    if m:
        return f'第{m.group(1)}批药品限适应症'

    # Handle numbered types like "9、药品限二线使用" → "药品限二线使用"
    m = re.match(r'\d+[、，]?\s*(.+)', rt)
    if m:
        rt = m.group(1)

    # Check known mappings
    for key, (short, basis) in RULE_TYPE_MAP.items():
        if key in rt:
            return short

    # Default: take first meaningful part
    parts = re.split(r'[、，-]', rt)
    for p in parts:
        p = p.strip()
        if len(p) >= 4 and not p.isdigit():
            return p
    return rt[:20]

def generate_basis(rule_type, check_logic):
    """Generate logic_basis based on rule type"""
    # Check known mappings
    for key, (short, basis) in RULE_TYPE_MAP.items():
        if key in rule_type:
            return basis

    # Batch indication rules
    if '批药品限适应症' in rule_type or '药品限适应症' in rule_type:
        return '根据国家医保局药品支付标准，该药品限定特定适应症支付'

    # Second-line
    if '二线' in rule_type:
        return '根据医保药品目录，该药品需一线药物治疗无效方可使用'

    # Internet hospital
    if '互联网' in rule_type:
        return '根据医保药品目录，该药品限互联网医院特定范围使用'

    # Herbal pieces
    if '饮片' in rule_type:
        if '单复方' in rule_type:
            return '根据医保药品目录，该中药饮片单方/复方使用不予支付'
        return '根据医保药品目录，该中药饮片使用不予支付'

    # Default based on check_logic
    if '与限定性别不符' in check_logic:
        return '根据医保药品目录，该药品限定特定性别使用'
    if '超儿童' in check_logic or '儿童年龄' in check_logic:
        return '根据医保药品目录，该药品限定儿童使用'
    if '医疗机构级别' in check_logic:
        return '根据医保药品目录，该药品限定在特定级别医疗机构使用'
    if '就医方式' in check_logic:
        return '根据医保药品目录，该药品限定特定就医方式'
    if '一线' in check_logic:
        return '根据医保药品目录，该药品需一线药物治疗无效方可使用'
    if '适应症' in check_logic:
        return '根据国家医保局药品支付标准，该药品限定特定适应症支付'
    if '支付疗程' in check_logic:
        return '根据医保药品目录，该药品限定支付天数/疗程'

    return '参见国家医保药品目录及相关支付政策'

def main():
    print("=" * 60)
    print("修复审核规则：精简类别 + 生成依据")
    print("=" * 60)

    # Load audit_rules
    with open(os.path.join(BASE, 'audit_rules.json'), 'r', encoding='utf-8') as f:
        rules = json.load(f)

    # Fix each rule
    fixed = 0
    for r in rules:
        old_type = r.get('rule_type', '')
        new_type = shorten_type(old_type)
        if new_type != old_type:
            r['rule_type'] = new_type
            fixed += 1
        # Generate basis if empty
        if not r.get('logic_basis', ''):
            r['logic_basis'] = generate_basis(old_type, r.get('check_logic', ''))

    print(f"  精简类别: {fixed} 条")
    print(f"  生成依据: {len(rules)} 条")

    # Save
    with open(os.path.join(BASE, 'audit_rules.json'), 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, 'audit_rules.json'), 'rb') as f_in:
        with gzip.open(os.path.join(BASE, 'audit_rules.json.gz'), 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    # Now update drugs.json rules
    print("\n[2] 更新 drugs.json 中的规则...")
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    # Build rule lookup by name → list of rules
    def normalize(s):
        return re.sub(r'[\s　（）()ⅠⅡⅢⅣⅤ]+', '', str(s)).lower() if s else ''

    rules_by_name = {}
    for r in rules:
        dn = normalize(r.get('drug_name', ''))
        if not dn: continue
        if dn not in rules_by_name:
            rules_by_name[dn] = []
        rules_by_name[dn].append(r)

    updated = 0
    for drug in drugs:
        drug_norm = normalize(drug.get('name', ''))
        if not drug_norm: continue

        matched = []
        # Exact
        if drug_norm in rules_by_name:
            matched = rules_by_name[drug_norm]
        # Substring
        if not matched:
            for rn, rlist in rules_by_name.items():
                if len(drug_norm) >= 2 and (drug_norm in rn or rn in drug_norm):
                    matched.extend(rlist)

        if matched:
            drug['rules'] = [{
                'drug': r.get('drug_name', ''),
                'category': r.get('rule_type', ''),
                'rule': r.get('check_logic', ''),
                'basis': r.get('logic_basis', ''),
                'code': r.get('drug_code', ''),
            } for r in matched]
            updated += 1

    print(f"  {updated} 个药品规则已更新")

    # Save
    with open(os.path.join(BASE, 'drugs.json'), 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, 'drugs.json'), 'rb') as f_in:
        with gzip.open(os.path.join(BASE, 'drugs.json.gz'), 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    # Sample
    print("\n样例:")
    for r in rules[:5]:
        print(f"  [{r['rule_type']}] {r.get('drug_name','')}")
        print(f"    依据: {r.get('logic_basis','')}")

    print("\n✅ 完成")

if __name__ == '__main__':
    main()
