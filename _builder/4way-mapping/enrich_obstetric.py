"""Enrich new SH items with obstetric policy data."""
import json, gzip, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.dirname(BASE)

# 1. Extract obstetric policy data
f = os.path.join(BUILDER, '上海产科类医疗服务价格项目.xlsx')
with open(f, 'r', encoding='utf-8') as fh:
    html = fh.read()

rows_match = re.findall(
    r'<tr[^>]*>(.*?)</tr>',
    re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL).group(1),
    re.DOTALL
)

ob_data = {}  # code or name -> {output, cost, unit, price3, price2, price1, notes, payment}
for i in range(3, len(rows_match)):
    cells = re.findall(r'<td[^>]*>(.*?)</td>', rows_match[i], re.DOTALL)
    if len(cells) < 8:
        continue

    code = re.sub(r'<[^>]+>', '', cells[1]).strip() if len(cells) > 1 else ''
    name = re.sub(r'<[^>]+>', '', cells[2]).strip() if len(cells) > 2 else ''

    # Skip section headers (like "产科孕产系统")
    if not code.startswith('01') and not ('扩展' in name or '加收' in name):
        continue

    output = re.sub(r'<[^>]+>', '', cells[3]).strip() if len(cells) > 3 else ''
    cost = re.sub(r'<[^>]+>', '', cells[4]).strip() if len(cells) > 4 else ''
    unit = re.sub(r'<[^>]+>', '', cells[5]).strip() if len(cells) > 5 else ''
    price3 = re.sub(r'<[^>]+>', '', cells[6]).strip() if len(cells) > 6 else ''
    price2 = re.sub(r'<[^>]+>', '', cells[7]).strip() if len(cells) > 7 else ''
    price1 = re.sub(r'<[^>]+>', '', cells[8]).strip() if len(cells) > 8 else ''
    notes = re.sub(r'<[^>]+>', '', cells[9]).strip() if len(cells) > 9 else ''
    payment = re.sub(r'<[^>]+>', '', cells[10]).strip() if len(cells) > 10 else ''

    info = {
        'output': output, 'cost': cost, 'unit': unit,
        'price3': price3, 'price2': price2, 'price1': price1,
        'notes': notes, 'payment': payment,
    }

    if code:
        ob_data[code] = info
    if name and ('扩展' in name or '加收' in name):
        ob_data[name] = info

print(f"Obstetric policy items extracted: {len(ob_data)}")
for code, info in list(ob_data.items())[:5]:
    print(f"  {code}: 三级{info['price3']}/二级{info['price2']}/一级{info['price1']} {info['unit']} {info['payment']}")

# 2. Load data.json
with open(os.path.join(BASE, 'data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# 3. Enrich new SH items
enriched = 0
for s in data['shanghai_new']:
    code = s.get('code', '')
    name = s.get('name', '')

    # Try exact code match
    matched = None
    if code in ob_data:
        matched = ob_data[code]
    elif name in ob_data:
        matched = ob_data[name]
    elif code:
        # Fuzzy: try base code match (first 13 chars)
        for pcode, pd in ob_data.items():
            if len(pcode) >= 13 and code[:13] == pcode[:13]:
                matched = pd
                break

    if matched:
        s['output'] = matched['output']
        s['cost_structure'] = matched['cost']
        s['unit'] = matched['unit']
        s['price_3'] = matched['price3']
        s['price_2'] = matched['price2']
        s['price_1'] = matched['price1']
        s['notes'] = matched['notes']
        s['payment'] = matched['payment']
        enriched += 1

print(f"\nEnriched: {enriched} new obstetric items")

# Count totals
rehab = sum(1 for s in data['shanghai_new'] if s.get('price_3') and s['code'].startswith('015'))
ob = sum(1 for s in data['shanghai_new'] if s.get('price_3') and s['code'].startswith('013'))
no = sum(1 for s in data['shanghai_new'] if not s.get('price_3'))
print(f"  Rehab: {rehab}, Obstetric: {ob}, Not enriched: {no}")

# Sample
for s in data['shanghai_new']:
    if s.get('price_3') and s['code'].startswith('013'):
        print(f"\n  Sample: {s['name'][:40]}")
        print(f"    价格: 三级{s.get('price_3')} / 二级{s.get('price_2')} / 一级{s.get('price_1')} /{s.get('unit')}")
        print(f"    支付: {s.get('payment')}")
        break

# Save
with open(os.path.join(BASE, 'data.json'), 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
jbytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
with gzip.open(os.path.join(BASE, 'data.json.gz'), 'wb', compresslevel=6) as f:
    f.write(jbytes)
print(f"\nSaved. Total new SH: {len(data['shanghai_new'])}")
