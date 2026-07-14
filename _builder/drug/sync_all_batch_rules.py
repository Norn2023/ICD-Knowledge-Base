"""
Comprehensive script to parse and sync ALL batch rules to drugs.json
Handles batches 9-15 and special category rules
"""
import json, os, re, gzip, sys, openpyxl, fitz
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def parse_pdf_rules(pdf_path):
    """Generic PDF rule parser for batch format"""
    doc = fitz.open(pdf_path)
    text = ''
    for i in range(doc.page_count):
        text += doc[i].get_text()

    lines = text.split('\n')
    rules = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r'^\d{1,3}$', line):
            try:
                seq = int(line)
            except:
                i += 1
                continue
            if seq < 1 or seq > 200:
                i += 1
                continue
            i += 1
            # Get drug name (may span lines)
            drug_parts = []
            found_logic = False
            while i < len(lines):
                curr = lines[i].strip()
                if '使用' in curr and ('药品' in curr or '该药' in curr):
                    # This line contains the detection logic
                    # Drug name was in previous lines
                    found_logic = True
                    i += 1
                    break
                elif re.match(r'^\d{1,3}$', curr) or '第九批' in curr or '第十批' in curr or '合计' in curr:
                    break
                elif '第 ' in curr and '页' in curr:
                    i += 1
                    continue
                elif '知识点' in curr or '药品限' in curr or '药品代码' in curr:
                    i += 1
                    continue
                else:
                    drug_parts.append(curr)
                    i += 1

            if not drug_parts:
                continue

            drug_name = ''.join(drug_parts).strip()
            # Clean up drug name - remove any trailing logic text
            for keyword in ['使用药品的疾病诊断不符合', '使用了该药品', '限定支付适应症']:
                if keyword in drug_name:
                    drug_name = drug_name.split(keyword)[0].strip()

            if not drug_name or len(drug_name) < 2:
                continue

            # Find limit text - starts with 限
            limit_parts = []
            while i < len(lines):
                curr = lines[i].strip()
                if re.match(r'^\d{1,3}$', curr):
                    if limit_parts:
                        break
                    else:
                        i += 1
                        continue
                if any(kw in curr for kw in ['第九批', '第十批', '第十一批', '第十二批', '第十三批', '第十四批', '第十五批', '第十六批', '合计']):
                    break
                if '第 ' in curr and '页' in curr:
                    i += 1
                    continue
                if '知识点' in curr and '代码' in curr:
                    i += 1
                    continue
                if '逻辑依据' in curr or '限定支付适应症' in curr:
                    i += 1
                    continue
                if curr.startswith('限') or (limit_parts and len(curr) > 3):
                    limit_parts.append(curr)
                    i += 1
                    # Check if next line is a code count (just digits)
                    if i < len(lines) and re.match(r'^\d+$', lines[i].strip()):
                        break
                else:
                    if limit_parts:
                        break
                    i += 1

            limit_text = ' '.join(limit_parts).strip()
            # Clean up remaining fragments
            limit_text = re.sub(r'\s+', ' ', limit_text)
            if limit_text and drug_name:
                rules[drug_name] = limit_text
        else:
            i += 1
    return rules


# === PARSE ALL BATCHES ===
all_rules = {}

# Batch 12 - Excel format (5 cols with rules embedded)
print('Parsing batch 12...')
try:
    wb = openpyxl.load_workbook(os.path.join(BASE, '12、12批药品限适应症-57个药633个代码（消化道和代谢）/20260523第十二批“药品限适应症”规则对应部分知识点明细.xlsx'))
    ws = wb.active
    rules = {}
    for r in range(5, ws.max_row+1):
        name = ws.cell(r, 2).value
        logic = ws.cell(r, 4).value
        if name and str(name).strip() and logic and str(logic).strip():
            rules[str(name).strip()] = str(logic).strip()
    all_rules['batch12_消化代谢'] = rules
    print(f'  batch12: {len(rules)} rules')
except Exception as e:
    print(f'  batch12 ERROR: {e}')

# Batch 13 - Excel format
print('Parsing batch 13...')
try:
    wb = openpyxl.load_workbook(os.path.join(BASE, '13、13批次药品适应症-66个药1296个代谢(血液和造血器官）/20250601第十三批“药品限适应症”规则对应知识点明细.xlsx'))
    ws = wb.active
    rules = {}
    for r in range(5, ws.max_row+1):
        name = ws.cell(r, 2).value
        logic = ws.cell(r, 4).value
        if name and str(name).strip() and logic and str(logic).strip():
            rules[str(name).strip()] = str(logic).strip()
    all_rules['batch13_血液造血'] = rules
    print(f'  batch13: {len(rules)} rules')
except Exception as e:
    print(f'  batch13 ERROR: {e}')

# Batch 14 - Excel format
print('Parsing batch 14...')
try:
    wb = openpyxl.load_workbook(os.path.join(BASE, '14、14批次药品适应症-43个药物1008个代码（心血管系统）/20260609第十四批“药品限适应症”规则对应部分知识点明细（43条）.xlsx'))
    ws = wb.active
    rules = {}
    for r in range(5, ws.max_row+1):
        name = ws.cell(r, 2).value
        logic = ws.cell(r, 4).value
        if name and str(name).strip() and logic and str(logic).strip():
            rules[str(name).strip()] = str(logic).strip()
    all_rules['batch14_心血管'] = rules
    print(f'  batch14: {len(rules)} rules')
except Exception as e:
    print(f'  batch14 ERROR: {e}')

# Batch 15 - PDF format
print('Parsing batch 15...')
try:
    rules = parse_pdf_rules(os.path.join(BASE, '15、15批次药品适应症-34个药物452个代码（生殖内分泌激素）/20260616第十五批“药品限适应症”规则对应知识点明细.pdf'))
    all_rules['batch15_生殖内分泌'] = rules
    print(f'  batch15: {len(rules)} rules')
except Exception as e:
    print(f'  batch15 ERROR: {e}')

# Batch 9 - 限二线使用 PDF
print('Parsing batch 9 (限二线)...')
try:
    rules = parse_pdf_rules(os.path.join(BASE, '9、药品限二线使用/20260421第九批 “药品限二线使用”规则对应知识点明细.pdf'))
    all_rules['batch9_限二线'] = rules
    print(f'  batch9: {len(rules)} rules')
except Exception as e:
    print(f'  batch9 ERROR: {e}')

# Save all parsed rules
with open(os.path.join(BASE, 'all_batch_rules.json'), 'w', encoding='utf-8') as f:
    json.dump(all_rules, f, ensure_ascii=False, indent=2)

# === SYNC TO drugs.json ===
print('\n=== Syncing to drugs.json ===')
with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
    drugs = json.load(f)

# Build name index
drug_by_name = {}
for d in drugs:
    drug_by_name[d['name']] = d

# Build a mapping for fuzzy names
def normalize_name(n):
    return re.sub(r'[\s　()（）ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+', '', str(n)).lower()

norm_index = {}
for d in drugs:
    norm_index[normalize_name(d['name'])] = d['name']

total_synced = 0
batch_counts = {}

for batch_label, rules in all_rules.items():
    batch_synced = 0
    for rule_name, rule_text in rules.items():
        target = None
        rn = rule_name.strip()
        rn_norm = normalize_name(rn)

        # Exact match
        if rn in drug_by_name:
            target = rn
        # Normalized match
        elif rn_norm in norm_index:
            target = norm_index[rn_norm]
        else:
            # Substring match
            for dname, d in drug_by_name.items():
                dn_norm = normalize_name(dname)
                if len(rn_norm) > 4 and len(dn_norm) > 4:
                    if rn_norm in dn_norm or dn_norm in rn_norm:
                        target = dname
                        break

        if target:
            drug_by_name[target]['note'] = rule_text
            drug_by_name[target][f'_rule_{batch_label}'] = True
            batch_synced += 1
            total_synced += 1

    batch_counts[batch_label] = {'total': len(rules), 'synced': batch_synced}
    print(f'  {batch_label}: {batch_synced}/{len(rules)} synced')

# Save
with open(os.path.join(BASE, 'drugs.json'), 'w', encoding='utf-8') as f:
    json.dump(drugs, f, ensure_ascii=False, indent=1)
with open(os.path.join(BASE, 'drugs.json'), 'rb') as f_in:
    with gzip.open(os.path.join(BASE, 'drugs.json.gz'), 'wb', compresslevel=9) as f_out:
        f_out.write(f_in.read())

print(f'\nTotal drugs synced: {total_synced}')
print('Saved drugs.json and drugs.json.gz')

# Count total drugs with any rule note
note_count = sum(1 for d in drugs if d.get('note'))
print(f'Total drugs with rule notes: {note_count}')
