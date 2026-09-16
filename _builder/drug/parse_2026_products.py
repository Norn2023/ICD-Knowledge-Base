"""
Parse 医保药品分类与代码数据(截至2026年6月5日).pdf
Find drug names NOT in 2025 catalog → candidates for addition.
"""
import fitz, json, sys, os, gzip, re, time
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    return re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+', '', str(s))

def main():
    t0 = time.time()
    print("=" * 60)
    print("2026医保分类数据 × 2025目录 交叉比对")
    print("=" * 60)

    # Load 2025 catalog names
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    existing = set()
    for d in drugs:
        n = norm(d.get('name', ''))
        if n and len(n) >= 2: existing.add(n)
        for v in d.get('variants', []):
            rn = norm(str(v.get('reg_name', '')))
            if rn and len(rn) >= 2: existing.add(rn)
    print(f"2025目录已有品名: {len(existing)}")

    # Open PDF
    pdf_path = None
    for f in os.listdir(BASE):
        if '医保药品分类' in f and '2026' in f and f.endswith('.pdf'):
            pdf_path = os.path.join(BASE, f)
            break
    doc = fitz.open(pdf_path)
    total = doc.page_count
    print(f"PDF: {total} 页")

    # Strategy: extract all product reg_names by looking for drug codes (X...)
    # and the Chinese text that follows them (the reg_name)
    new_drugs = Counter()  # reg_name → count
    total_prods = 0

    for p_idx in range(total):
        t = doc[p_idx].get_text()
        # Find all drug codes and the text between them
        # Drug code pattern: line starting with X + 20+ alphanumeric chars
        lines = t.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Check if this is a drug code (skip page headers, etc.)
            if re.match(r'^X[A-Z0-9]{18,}', line) and len(line) >= 20:
                total_prods += 1
                # Get the reg_name: lines after the code until we hit a dosage form or next code
                reg_parts = []
                j = i + 1
                while j < len(lines) and j < i + 8:
                    nl = lines[j].strip()
                    if re.match(r'^X[A-Z0-9]{18,}', nl):
                        break  # next product
                    # Skip if this looks like a dosage form line
                    is_form = re.match(r'^(胶囊剂|片剂|注射液|注射剂|颗粒剂|口服|乳膏剂|滴眼剂|滴耳液|喷雾剂|气雾剂|吸入剂|栓剂|丸剂|散剂|贴剂|洗剂|搽剂|凝胶剂|糖浆剂|混悬剂|软膏剂|眼膏剂|膜剂|酊剂|擦剂|粉雾剂|干混悬剂|泡腾片|含片|咀嚼片|分散片|缓释片|控释片|肠溶片|口崩片|舌下片|阴道片|植入剂|贴膏剂|膏药剂)', nl)
                    if is_form:
                        break
                    # Skip pure numbers, units, codes
                    if re.match(r'^[\d\s\.\-\+]+$', nl):
                        break
                    if re.match(r'^(无|片|粒|支|瓶|盒|袋|包)$', nl):
                        break
                    if re.match(r'^(国药准字|塑料|铝塑|玻璃|PVC|PE|聚)', nl):
                        break
                    # This looks like part of a drug name (Chinese chars)
                    if re.search(r'[一-鿿]', nl):
                        # Accept if it contains Chinese (even mixed with ASCII for complex names)
                        if not re.match(r'^(甲|乙)$', nl):
                            reg_parts.append(nl)
                    j += 1

                if reg_parts:
                    # Join continuous reg name parts
                    reg_name = ''.join(reg_parts)
                    reg_name = re.sub(r'\s+', '', reg_name)  # remove whitespace
                    n = norm(reg_name)
                    if n and len(n) >= 2 and n not in existing:
                        new_drugs[reg_name] += 1

                i = j  # Skip to next product
                continue
            i += 1

        if (p_idx + 1) % 2000 == 0:
            elapsed = time.time() - t0
            print(f"  {p_idx+1}/{total} ({elapsed:.0f}s) products:{total_prods} new:{len(new_drugs)}")

    doc.close()
    elapsed = time.time() - t0
    print(f"\nDone: {elapsed:.0f}s, {total_prods} products, {len(new_drugs)} new drug names")

    # Show top new drugs
    print(f"\n=== 2026有但2025目录无的药品 (前80) ===")
    for name, cnt in new_drugs.most_common(80):
        print(f"  {name} ({cnt} products)")

    # Save
    out = [{'name': k, 'products': v} for k, v in new_drugs.most_common()]
    out_path = os.path.join(BASE, 'new_drugs_2026.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nSaved: {out_path} ({len(out)} drugs)")

if __name__ == '__main__':
    main()
