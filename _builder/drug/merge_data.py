"""
Merge drugs.json + PDF products + Audit Rules into final output
Improved matching: substring-based name matching + batch processing
"""
import json, sys, os, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DRUGS_JSON = 'D:/AI_libra/codex_Obsi/_builder/drug/drugs.json'
PDF_PRODUCTS = 'D:/AI_libra/codex_Obsi/_builder/drug/pdf_products.json'
AUDIT_RULES = 'D:/AI_libra/codex_Obsi/_builder/drug/audit_rules.json'
OUTPUT_JSON = 'D:/AI_libra/codex_Obsi/_builder/drug/final_drug_catalog.json'
OUTPUT_MD = 'D:/AI_libra/codex_Obsi/_builder/drug/final_drug_catalog.md'

def clean_std_code(text):
    if not text: return ''
    m = re.search(r'(\d{14,})', text)
    return m.group(1) if m else text.strip()

def clean_approval(text):
    if not text: return ''
    m = re.search(r'(国药[准字包字][^\s]+)', text)
    return m.group(1) if m else text.strip()

def normalize_name(name):
    if not name: return ''
    return name.strip().replace(' ', '').replace('　', '')

def clean_pdf_name(name):
    """Remove duplicates from PDF name caused by merged cells"""
    if not name: return ''
    # Remove the header contamination
    name = name.replace('注册名称', '')
    # Check for repeated patterns (same name repeated 2+ times)
    # Strategy: try to find the shortest repeating unit
    for length in range(1, len(name) // 2 + 1):
        segment = name[:length]
        if len(name) % length == 0 and all(name[i:i+length] == segment for i in range(0, len(name), length)):
            # It's cleanly repeated. Use the first occurrence.
            return segment
    # Try another approach: find the most frequent substring of reasonable length
    # Simple heuristic: take the first half and see if the second half matches
    mid = len(name) // 2
    if name[:mid] == name[mid:2*mid]:
        return name[:mid]
    return name

def main():
    print("=" * 60)
    print("医保药品全目录 - 数据合并 v2")
    print("=" * 60)

    # 1. Load drugs.json
    print("\n[1/5] 加载 drugs.json...")
    with open(DRUGS_JSON, 'r', encoding='utf-8') as f:
        drug_catalog = json.load(f)
    print(f"  ✓ {len(drug_catalog)} 条药品目录记录")

    # 2. Load PDF products
    print("[2/5] 加载 PDF 产品数据...")
    with open(PDF_PRODUCTS, 'r', encoding='utf-8') as f:
        pdf_products = json.load(f)
    print(f"  ✓ {len(pdf_products)} 条产品规格记录")

    # Clean PDF names and filter headers
    print("     清理 PDF 名称...")
    cleaned_products = []
    dirty_names = 0
    for p in pdf_products:
        raw_name = p.get('注册名称', '')
        if not raw_name or raw_name == '注册名称':
            continue
        clean_name = clean_pdf_name(raw_name)
        if clean_name != raw_name:
            dirty_names += 1
        p['注册名称_clean'] = clean_name
        p['药品本位码_clean'] = clean_std_code(p.get('药品本位码', ''))
        p['批准文号_clean'] = clean_approval(p.get('批准文号', ''))
        cleaned_products.append(p)
    print(f"     ✓ 清理了 {dirty_names} 个重复名称")
    pdf_products = cleaned_products

    # 3. Load audit rules
    print("[3/5] 加载审核规则...")
    with open(AUDIT_RULES, 'r', encoding='utf-8') as f:
        audit_rules = json.load(f)
    print(f"  ✓ {len(audit_rules)} 条审核规则")

    # 4. Build lookup indices
    print("[4/5] 构建索引...")

    # Index PDF products by clean name
    pdf_by_name = defaultdict(list)
    pdf_unique_names = set()
    for p in pdf_products:
        name = normalize_name(p.get('注册名称_clean', ''))
        if name:
            pdf_by_name[name].append(p)
            pdf_unique_names.add(name)
    print(f"     ✓ PDF 共 {len(pdf_unique_names)} 个唯一药物名")

    # Index audit rules by drug name
    rules_by_name = defaultdict(list)
    rules_unique_names = set()
    for r in audit_rules:
        dn = normalize_name(r.get('drug_name', ''))
        dc = r.get('drug_code', '')
        if dn:
            rules_by_name[dn].append(r)
            rules_unique_names.add(dn)
    print(f"     ✓ 规则共 {len(rules_unique_names)} 个唯一药物名")

    # Also index rules by drug code
    rules_by_code = defaultdict(list)
    for r in audit_rules:
        dc = r.get('drug_code', '')
        if dc and len(dc) >= 15:
            rules_by_code[dc].append(r)
    rules_by_prod_code = defaultdict(list)  # for 15-digit drug codes in PDF
    for r in audit_rules:
        dc = r.get('drug_code', '')
        if dc and len(dc) >= 15:
            rules_by_prod_code[dc].append(r)

    # 5. Match drugs
    print("[5/5] 匹配数据...")

    final_output = []
    match_stats = {'exact': 0, 'substring': 0, 'no_match': 0}
    total_products_matched = 0
    total_rules_matched = 0

    for drug in drug_catalog:
        drug_name_raw = drug.get('name', '')
        drug_name = normalize_name(drug_name_raw)
        if not drug_name:
            continue

        # Generate alternative names for matching
        alt_names = set()
        alt_names.add(drug_name)

        # Handle bracketed names: "埃索美拉唑(艾司奥美拉唑)" → try both
        bracket_pattern = re.findall(r'[^(]+\(([^)]+)\)', drug_name)
        for alt in bracket_pattern:
            alt_names.add(normalize_name(alt))
        # Also try the part before the first bracket
        first_part = drug_name.split('(')[0].strip()
        if first_part and first_part != drug_name:
            alt_names.add(normalize_name(first_part))

        # Handle compound names with spaces: "补液盐Ⅰ 补液盐Ⅱ 补液盐Ⅲ"
        parts = drug_name.split()
        if len(parts) > 1:
            for part in parts:
                # Remove roman numerals at end
                clean_part = re.sub(r'[ⅠⅡⅢⅣⅤⅥ]+$', '', part).strip()
                if clean_part and len(clean_part) >= 2:
                    alt_names.add(normalize_name(clean_part))

        # Handle Ⅱ suffix: "二甲双胍二甲双胍Ⅱ"
        # Try removing the Ⅱ/Ⅲ suffix
        simplified = re.sub(r'[ⅠⅡⅢⅣⅤⅥ]+$', '', drug_name)
        if simplified != drug_name:
            alt_names.add(normalize_name(simplified))

        # Try to match PDF products
        matched_products = []
        matched_by_exact = False

        # Strategy 1: Exact match with any alt name
        for alt in alt_names:
            if alt in pdf_by_name:
                matched_products = pdf_by_name[alt]
                matched_by_exact = True
                break

        if not matched_by_exact:
            # Strategy 2: Substring matching with all alt names
            seen_codes = set()
            for alt in alt_names:
                if len(alt) < 2:
                    continue
                for pdf_name, prods in pdf_by_name.items():
                    if alt in pdf_name or pdf_name in alt:
                        if len(pdf_name) >= 2:
                            for p in prods:
                                code = p.get('药品代码', '')
                                if code not in seen_codes:
                                    seen_codes.add(code)
                                    matched_products.append(p)

        if matched_by_exact:
            match_stats['exact'] += 1
        elif matched_products:
            match_stats['substring'] += 1
        else:
            match_stats['no_match'] += 1

            # Deduplicate
            seen_codes = set()
            deduped = []
            for p in matched_products:
                code = p.get('药品代码', '')
                if code not in seen_codes:
                    seen_codes.add(code)
                    deduped.append(p)
            matched_products = deduped

            if matched_products:
                match_stats['substring'] += 1
            else:
                match_stats['no_match'] += 1

        total_products_matched += len(matched_products)

        # Match audit rules
        matched_rules = []
        # By drug name
        if drug_name in rules_by_name:
            matched_rules.extend(rules_by_name[drug_name])
        # By drug name substring in rules
        for rule_name, rules in rules_by_name.items():
            if drug_name != rule_name and (drug_name in rule_name or rule_name in drug_name):
                for r in rules:
                    if r not in matched_rules:
                        matched_rules.append(r)
        # By product code
        for prod in matched_products:
            for code_field in ['药品代码', '药品本位码_clean']:
                code = prod.get(code_field, '')
                if code and code in rules_by_prod_code:
                    for r in rules_by_prod_code[code]:
                        if r not in matched_rules:
                            matched_rules.append(r)

        total_rules_matched += len(matched_rules)

        # Build entry
        entry = {
            'drug_name': drug.get('name', ''),
            'drug_type': drug.get('type', ''),
            'classification_code': drug.get('code', ''),
            'classification_path': ' › '.join(filter(None, [
                drug.get('cat', ''), drug.get('subcat', ''),
                drug.get('subsubcat', '')
            ])),
            'insurance_level': drug.get('level', ''),
            'insurance_note': drug.get('note', ''),
            'limit_type': drug.get('limit_type', ''),
            'form': drug.get('form', ''),
            'essential': drug.get('essential', False),
            'products': matched_products,
            'audit_rules': matched_rules,
        }
        final_output.append(entry)

    # Statistics
    total_drugs = len(final_output)
    print(f"\n{'=' * 60}")
    print("合并统计")
    print(f"{'=' * 60}")
    print(f"  药物目录: {total_drugs} 条")
    print(f"  精确匹配: {match_stats['exact']} ({match_stats['exact']/total_drugs*100:.1f}%)")
    print(f"  子串匹配: {match_stats['substring']} ({match_stats['substring']/total_drugs*100:.1f}%)")
    print(f"  无匹配:   {match_stats['no_match']} ({match_stats['no_match']/total_drugs*100:.1f}%)")
    print(f"  产品规格: {total_products_matched} 条")
    print(f"  匹配规则: {total_rules_matched} 条")
    print(f"  有匹配产品药物: {total_drugs - match_stats['no_match']} 条")

    # Save JSON
    print(f"\n保存 JSON...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=1)
    print(f"  ✓ {OUTPUT_JSON}")

    # Generate Markdown
    print(f"生成 Markdown...")
    generate_markdown(final_output)
    print(f"  ✓ {OUTPUT_MD}")

    print("\n✅ 完成!")

def generate_markdown(data):
    """Generate Markdown summary"""
    from collections import Counter
    lines = [
        "# 医保药品全目录（含代码、规格、审核规则）\n",
        f"> 数据来源：医保药品分类与代码数据(西药、中成药)截至2026年6月5日\n",
        f"> 药品目录：{len(data)} 条 | 审核规则来源：15 类\n",
        "---\n",
    ]

    # Drugs with most audit rules
    sorted_by_rules = sorted(data, key=lambda x: len(x['audit_rules']), reverse=True)
    lines.append("## 审核规则最多的药物 Top 30\n")
    lines.append("| 药品名称 | 类型 | 医保级别 | 规格数 | 审核规则数 | 规则类型 |\n")
    lines.append("|---------|------|---------|-------|-----------|--------|\n")

    count = 0
    for drug in sorted_by_rules:
        if not drug['audit_rules']:
            continue
        count += 1
        if count > 30:
            break
        rule_types = defaultdict(int)
        for r in drug['audit_rules']:
            rt = r.get('rule_type', '').split('、')[-1] if '、' in r.get('rule_type', '') else r.get('rule_type', '')
            rule_types[rt] += 1
        types_str = ', '.join([f"{k}({v})" for k, v in sorted(rule_types.items(), key=lambda x: -x[1])[:3]])
        lines.append(f"| {drug['drug_name']} | {drug['drug_type']} | {drug['insurance_level']}类 | {len(drug['products'])} | {len(drug['audit_rules'])} | {types_str} |\n")

    # Drug detail samples
    lines.append("\n---\n## 药物详情样例\n")
    sample_count = 0
    for drug in data:
        if not drug['products']:
            continue
        sample_count += 1
        if sample_count > 5:
            break

        lines.append(f"### {drug['drug_name']}\n")
        lines.append(f"- **类型**: {drug['drug_type']} | **医保级别**: {drug['insurance_level']}类 | **分类**: {drug['classification_code']}\n")
        lines.append(f"- **分类路径**: {drug['classification_path']}\n")
        if drug['insurance_note']:
            lines.append(f"- **医保备注**: {drug['insurance_note']}\n")
        if drug['limit_type']:
            lines.append(f"- **限定类型**: {drug['limit_type']}\n")

        # Products table
        lines.append(f"\n#### 产品规格 ({len(drug['products'])} 个)\n")
        lines.append("| 药品代码 | 剂型 | 注册规格 | 包装 | 企业 | 批准文号 | 本位码 |\n")
        lines.append("|---------|------|---------|------|------|---------|-------|\n")
        for prod in drug['products'][:10]:
            lines.append(f"| {prod.get('药品代码','')} | {prod.get('注册剂型','')} | {prod.get('注册规格','')} | {prod.get('最小包装数量','')}{prod.get('最小包装单位','')} | {prod.get('药品企业','')[:20]} | {prod.get('批准文号_clean','')} | {prod.get('药品本位码_clean','')} |\n")
        if len(drug['products']) > 10:
            lines.append(f"| ... | ... (共 {len(drug['products'])} 个) | ... | ... | ... | ... | ... |\n")

        # Audit Rules
        if drug['audit_rules']:
            lines.append(f"\n#### 适用审核规则 ({len(drug['audit_rules'])} 条)\n")
            lines.append("| 规则类型 | 检出逻辑 | 逻辑依据 |\n")
            lines.append("|---------|---------|---------|\n")
            for rule in drug['audit_rules'][:8]:
                rt = rule.get('rule_type', '').split('、')[-1] if '、' in rule.get('rule_type', '') else rule.get('rule_type', '')
                lines.append(f"| {rt} | {rule.get('check_logic','')} | {rule.get('logic_basis','')[:60]} |\n")
            if len(drug['audit_rules']) > 8:
                lines.append(f"| ... | (共 {len(drug['audit_rules'])} 条) | ... |\n")
        lines.append("\n---\n")

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == '__main__':
    main()
