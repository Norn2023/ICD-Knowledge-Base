"""
Tag negotiation drugs (国谈药品) in drugs.json.
Sources: 谈判药(西药), 谈判药(中成药), 竞价药品 sheets from 2025 catalog Excel.
"""
import json, sys, os, gzip, re
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    if not s: return ''
    return re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+', '', str(s))

def main():
    print("=" * 60)
    print("标注国谈药品")
    print("=" * 60)

    # Load Excel
    excel = os.path.join(BASE, '国家基本医疗保险、生育保险和工伤保险药品目录（2025年）.xlsx')
    wb = openpyxl.load_workbook(excel, read_only=True, data_only=True)

    # Extract negotiation drug names from all relevant sheets
    nego_names = set()  # normalized
    nego_data = {}      # normalized → {name, type, note, period}

    for sn in ['谈判药（西药） ', '谈判药（中成药）', '竞价药品']:
        ws = wb[sn]
        rows = list(ws.iter_rows(values_only=True))
        for row in rows:
            vals = [str(v).strip() if v else '' for v in row]
            if len(vals) >= 8:
                code = vals[6]
                name = vals[7]
                if code and code.isdigit() and name:
                    note = vals[9] if len(vals) > 9 else ''
                    period = vals[10] if len(vals) > 10 else ''
                    ntype = '西药' if '西药' in sn else '中成药'
                    nn = norm(name)
                    nego_names.add(nn)
                    if nn not in nego_data:
                        nego_data[nn] = {'name': name, 'type': ntype, 'note': note, 'period': period, 'sheet': sn}

    # Also add 商业健康保险创新药品
    ws = wb['商业健康保险创新药品']
    rows = list(ws.iter_rows(values_only=True))
    shangye_names = set()
    for row in rows:
        vals = [str(v).strip() if v else '' for v in row]
        if len(vals) >= 7:
            code = vals[5]
            name = vals[6]
            if code and code.isdigit() and name:
                nn = norm(name)
                shangye_names.add(nn)
                if nn not in nego_data:
                    nego_data[nn] = {'name': name, 'type': '西药', 'note': '商业健康保险创新药', 'period': '', 'sheet': '商业健康保险创新药品'}

    wb.close()
    print(f"谈判西药+中成药+竞价: {len(nego_names)}")
    print(f"商业健康保险创新药: {len(shangye_names)}")

    # Load drugs
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    # Match and tag — exact normalized match only, no fuzzy fallback
    all_special = set(nego_names) | set(shangye_names)
    all_data = {}
    all_data.update(nego_data)
    matched = 0
    for d in drugs:
        name = d.get('name', '')
        n = norm(name)
        if n in all_special:
            d['negotiated'] = True
            d['nego_info'] = all_data.get(n, {})
            matched += 1

    # Count
    nego_count = sum(1 for d in drugs if d.get('negotiated'))
    print(f"\n匹配成功: {nego_count} drugs")

    # List unmatched negotiation drugs (not in drugs.json)
    matched_norms = set()
    for d in drugs:
        if d.get('negotiated'):
            matched_norms.add(norm(d.get('name', '')))
    unmatched = [(nn, nd) for nn, nd in all_data.items() if nn not in matched_norms]
    print(f"未匹配(国谈+竞价+商保): {len(unmatched)}")
    for nn, nd in unmatched[:20]:
        print(f"  {nd['name']} ({nd.get('type','')} {nd.get('sheet','')})")

    # Save
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print(f"\n✅ 标注完成: {nego_count} 个国谈药品")

if __name__ == '__main__':
    main()
