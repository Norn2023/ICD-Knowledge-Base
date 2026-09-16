"""Fix classification codes in drugs.json from Excel hierarchy"""
import json, sys, os, gzip, openpyxl

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
EXCEL = os.path.join(BASE, '国家基本医疗保险、生育保险和工伤保险药品目录（2025年）.xlsx')

def main():
    print("修复药品分类代码...")

    # Parse Excel to get code hierarchy
    wb = openpyxl.load_workbook(EXCEL, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[1]]
    rows = list(ws.iter_rows(values_only=True))

    # Build code hierarchy map: drug_name -> {cat_code, subcat_code, subsubcat_code, full_code}
    code_map = {}
    current_type = '西药'
    cat_code = ''; subcat_code = ''; subsubcat_code = ''

    for row in rows[1:]:  # skip header
        vals = [str(v).strip() if v else '' for v in row]
        code = vals[0] if len(vals) > 0 else ''
        cat_name = vals[1] if len(vals) > 1 else ''
        subcat_name = vals[2] if len(vals) > 2 else ''
        subsub_name = vals[3] if len(vals) > 3 else ''
        level = vals[5] if len(vals) > 5 else ''
        drug_name = vals[7] if len(vals) > 7 else ''

        if cat_name and ('中成药' in cat_name or '中药' in cat_name) and not code:
            current_type = '中成药'
            cat_code = ''; subcat_code = ''; subsubcat_code = ''
            continue

        if not drug_name and not level:
            if code and len(code) == 2:
                cat_code = code; subcat_code = ''; subsubcat_code = ''
                if code.startswith('Z'): current_type = '中成药'
                elif code.startswith('X'): current_type = '西药'
            elif code and len(code) == 4:
                subcat_code = code; subsubcat_code = ''
            elif code and len(code) in (5, 6):
                subsubcat_code = code
            continue

        if drug_name and drug_name != 'None' and level in ('甲', '乙'):
            parts = [c for c in [cat_code, subcat_code, subsubcat_code] if c]
            code_map[(current_type, drug_name)] = {
                'code': ' > '.join(parts) if parts else '',
                'cat_code': cat_code,
                'subcat_code': subcat_code,
                'subsubcat_code': subsubcat_code,
            }

    wb.close()
    print(f"  从Excel提取 {len(code_map)} 个药品代码映射")

    # Update drugs.json
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    updated = 0
    for d in drugs:
        key = (d.get('type', ''), d.get('name', ''))
        if key in code_map:
            cm = code_map[key]
            d['code'] = cm['code']
            d['cat_code'] = cm['cat_code']
            d['subcat_code'] = cm['subcat_code']
            d['subsubcat_code'] = cm['subsubcat_code']
            updated += 1

    print(f"  更新 {updated}/{len(drugs)} 个药品代码")

    # Save
    with open(os.path.join(BASE, 'drugs.json'), 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, 'drugs.json'), 'rb') as f_in:
        with gzip.open(os.path.join(BASE, 'drugs.json.gz'), 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    # Sample
    with_code = sum(1 for d in drugs if d.get('code'))
    print(f"  有代码的药品: {with_code}/{len(drugs)}")
    print("\n样例:")
    for d in drugs[:5]:
        print(f"  {d['name']}: code={d.get('code','无')}")
    print("\n✅ 完成")

if __name__ == '__main__':
    main()
