"""
FRESH rebuild: drugs.json from Excel + CLEAN PDF products only
"""
import json, sys, gzip, os, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE, '国家基本医疗保险、生育保险和工伤保险药品目录（2025年）.xlsx')
PDF_PATH = os.path.join(BASE, 'pdf_products.json')
OUTPUT = os.path.join(BASE, 'drugs.json')

def normalize(s):
    if not s: return ''
    return re.sub(r'[\s　（）()　]+', '', str(s)).lower()

def clean_repeated(s):
    """Fix PDF merged-cell artifacts: repeated substrings"""
    if not s or len(s) < 4:
        return s
    # For very short strings (2-3 chars), check for simple doubling
    if len(s) <= 6 and len(s) % 2 == 0:
        mid = len(s) // 2
        if s[:mid] == s[mid:]:
            return s[:mid]
    # For longer strings
    if len(s) < 8:
        return s
    # Strategy 1: exact repetition
    for unit_len in range(2, min(50, len(s)//2 + 1)):
        if len(s) % unit_len == 0 and s == s[:unit_len] * (len(s)//unit_len):
            return s[:unit_len]
    # Strategy 2: mid-split
    mid = len(s)//2
    if s[:mid] == s[mid:2*mid]:
        return s[:mid]
    # Strategy 3: sliding-window repeated substring
    for unit_len in range(2, min(40, len(s)//3 + 1)):
        for start in range(0, min(unit_len, 20)):
            if start + unit_len > len(s): continue
            unit = s[start:start+unit_len]
            count, pos = 1, start + unit_len
            while pos + unit_len <= len(s) and s[pos:pos+unit_len] == unit:
                count += 1; pos += unit_len
            if count >= 3 and pos >= len(s)*0.6:
                return s[:start] + unit
    # Strategy 4: truncate very long strings
    if len(s) > 200: return s[:200] + '…'
    return s

def is_clean_product(p):
    """Check if a PDF product record is usable (not heavily corrupted)"""
    name = str(p.get('注册名称', '')).strip()
    if not name or name == '注册名称' or len(name) > 80:
        return False
    # Only check the most corruption-prone fields
    pq = str(p.get('最小包装数量', '')).strip()
    if pq and len(pq) > 4: return False
    uprep = str(p.get('最小制剂单位', '')).strip()
    if uprep and len(uprep) > 3: return False
    upack = str(p.get('最小包装单位', '')).strip()
    if upack and len(upack) > 3: return False
    return True

def clean_field(val):
    """General field cleaning: strip garbage artifacts"""
    if not val: return ''
    val = str(val).strip()
    # Replace "无无" / "无无无" patterns (PDF artifact: doubling of 无)
    while '无无' in val:
        val = val.replace('无无', '无')
    # If it's just "无", treat as empty
    if val in ('无', 'None', 'null', '-'):
        return ''
    return val

def clean_barcode(val):
    """Extract clean 14-digit barcode from corrupted string"""
    if not val: return ''
    val = str(val).strip()
    digits = ''.join(c for c in val if c.isdigit())
    # Standard 药品本位码 is 14 digits
    if len(digits) >= 14:
        return digits[:14]
    elif len(digits) >= 10:
        return digits
    return ''

def clean_product(p):
    """Convert PDF product to clean variant dict"""
    code = str(p.get('药品代码', '')).strip()
    # If code is concatenated, extract first valid segment
    if len(code) > 25:
        m = re.match(r'(X[A-Z0-9]{15,24})', code)
        if m:
            code = m.group(1)
        else:
            code = code[:25]

    app = clean_repeated(str(p.get('批准文号', '')).strip())
    app = clean_field(app)
    # If approval has multiple numbers, extract first
    if app:
        approvals = re.findall(r'国药[准字包字]+[\w]+', app)
        if approvals and len(approvals) > 1:
            app = approvals[0]

    # Clean numeric fields
    pq = clean_repeated(str(p.get('最小包装数量', '')).strip())
    pq = clean_field(pq)
    if pq:
        pq_digits = ''.join(c for c in pq if c.isdigit())
        if pq_digits: pq = pq_digits

    uprep = clean_repeated(str(p.get('最小制剂单位', '')).strip())
    uprep = clean_field(uprep)

    upack = clean_repeated(str(p.get('最小包装单位', '')).strip())
    upack = clean_field(upack)

    return {
        'code': code,
        'reg_name': clean_field(clean_repeated(str(p.get('注册名称', '')).strip())),
        'reg_form': clean_field(clean_repeated(str(p.get('注册剂型', '')).strip())),
        'reg_spec': clean_field(clean_repeated(str(p.get('注册规格', '')).strip())),
        'trade_name': clean_field(clean_repeated(str(p.get('商品名称', '')).strip())),
        'dosage_form': clean_field(clean_repeated(str(p.get('剂型', '')).strip())),
        'spec': clean_field(clean_repeated(str(p.get('规格', '')).strip())),
        'pack_material': clean_field(clean_repeated(str(p.get('包装材质', '')).strip())),
        'pack_qty': pq,
        'unit_prep': uprep,
        'unit_pack': upack,
        'manufacturer': clean_field(clean_repeated(str(p.get('药品企业', '')).strip())),
        'approval': app,
        'barcode': clean_barcode(str(p.get('药品本位码', '')).strip()),
    }

def varkey(v):
    """Deduplication key for variants - use code, or name+mfr if code is bad"""
    code = v.get('code', '')
    if code and len(code) >= 15 and len(code) <= 25:
        return code
    # Use name + manufacturer as key for records with bad codes
    return normalize(v.get('reg_name', '')) + '|' + normalize(v.get('manufacturer', ''))

def main():
    print("=" * 60)
    print("药品数据从零重建 - 干净PDF数据")
    print("=" * 60)

    # Step 1: Parse Excel drug catalog
    print("\n[1/3] 解析 Excel 药品目录...")
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

    # Process combined sheet and 饮片
    # First parse the combined "西药和中成药及谈判药" sheet
    print("     解析: 西药和中成药及谈判药...")
    ws = wb[wb.sheetnames[1]]  # 西药和中成药及谈判药
    rows = list(ws.iter_rows(values_only=True))

    # Skip first row (title/header)
    data_start = 0
    for i, row in enumerate(rows):
        vals = [str(v).strip() if v else '' for v in row]
        # Look for header row with 级别 and 药品名称
        if any('级别' in v for v in vals if v) and any('药品名称' in v for v in vals if v):
            data_start = i + 1
            print(f"     找到表头在第 {i} 行，数据从第 {data_start} 行开始")
            break

    current_type = '西药'
    current_cat = ''
    current_subcat = ''
    current_subsubcat = ''
    current_cat_code = ''
    current_subcat_code = ''
    current_subsubcat_code = ''
    idx = 0
    drugs = []
    seen_names = set()

    for row in rows[data_start:]:
        vals = [str(v).strip() if v else '' for v in row]
        code = vals[0] if len(vals) > 0 else ''
        cat_name = vals[1] if len(vals) > 1 else ''
        subcat_name = vals[2] if len(vals) > 2 else ''
        subsub_name = vals[3] if len(vals) > 3 else ''
        level = vals[5] if len(vals) > 5 else ''
        drug_seq = vals[6] if len(vals) > 6 else ''
        drug_name = vals[7] if len(vals) > 7 else ''
        form = vals[8] if len(vals) > 8 else ''
        note = vals[9] if len(vals) > 9 else ''

        if cat_name and ('中成药' in cat_name or '中药' in cat_name) and not code:
            current_type = '中成药'
            current_cat = ''; current_subcat = ''; current_subsubcat = ''
            current_cat_code = ''; current_subcat_code = ''; current_subsubcat_code = ''
            continue

        if not any(vals): continue

        # Hierarchy detection - track codes at each level
        if not drug_name and not level:
            if code and len(code) == 2:
                current_cat_code = code
                current_cat = cat_name or ''
                current_subcat = ''; current_subsubcat = ''
                current_subcat_code = ''; current_subsubcat_code = ''
                if code.startswith('Z'): current_type = '中成药'
                elif code.startswith('X'): current_type = '西药'
            elif code and len(code) == 4:
                current_subcat_code = code
                current_subcat = subcat_name or cat_name or ''
                current_subsubcat = ''; current_subsubcat_code = ''
            elif code and len(code) in (5, 6):
                current_subsubcat_code = code
                current_subsubcat = subsub_name or subcat_name or ''
            continue

        # Drug row - build hierarchical code
        if drug_name and drug_name not in ('药品名称', 'None', '') and level in ('甲', '乙'):
            dedup_key = f"{current_type}|{drug_name}"
            if dedup_key in seen_names: continue
            seen_names.add(dedup_key)
            idx += 1

            # Build hierarchical code path
            code_parts = []
            if current_cat_code: code_parts.append(current_cat_code)
            if current_subcat_code: code_parts.append(current_subcat_code)
            if current_subsubcat_code: code_parts.append(current_subsubcat_code)
            full_code = ' > '.join(code_parts) if code_parts else ''

            drugs.append({
                'type': current_type,
                'code': full_code,
                'cat_code': current_cat_code,
                'subcat_code': current_subcat_code,
                'subsubcat_code': current_subsubcat_code,
                'cat': current_cat,
                'subcat': current_subcat,
                'subsubcat': current_subsubcat,
                'level': level,
                'id': idx,
                'name': drug_name,
                'form': form if form and form != 'None' and form != '*' else '',
                'note': note if note and note != 'None' else '',
                'essential': False,
                'variants': [],
                'rules': [],
            })

    # Parse 饮片 (herbal pieces)
    print("     解析: 饮片...")
    # Parse 饮片 (herbal pieces) - sheet index 9
    if len(wb.sheetnames) > 9:
        ws2 = wb[wb.sheetnames[9]]
        rows2 = list(ws2.iter_rows(values_only=True))
        current_cat = '中药饮片'
        for row in rows2:
            vals = [str(v).strip() if v else '' for v in row]
            seq = vals[0] if len(vals) > 0 else ''
            name = vals[1] if len(vals) > 1 else ''
            note = vals[2] if len(vals) > 2 else ''

            if name and name not in ('饮片名称', 'None', '') and seq.isdigit():
                dedup_key = f"中药饮片|{name}"
                if dedup_key in seen_names:
                    continue
                seen_names.add(dedup_key)
                idx += 1
                note_clean = note if note and note != 'None' else ''
                drugs.append({
                    'type': '中药饮片',
                    'code': seq,
                    'cat': current_cat,
                    'subcat': '',
                    'subsubcat': '',
                    'level': '甲',
                    'id': idx,
                    'name': name,
                    'form': '',
                    'note': note_clean,
                    'essential': False,
                    'variants': [],
                    'rules': [],
                })

    wb.close()
    print(f"  ✓ 共计 {len(drugs)} 条药品目录")

    # Step 2: Load and filter PDF products
    print("\n[2/3] 加载PDF产品数据（仅干净记录）...")
    with open(PDF_PATH, 'r', encoding='utf-8') as f:
        pdf_raw = json.load(f)

    clean_products = []
    skipped = 0
    for p in pdf_raw:
        if is_clean_product(p):
            clean_products.append(clean_product(p))
        else:
            skipped += 1
    print(f"  ✓ 干净: {len(clean_products)}, 跳过损坏: {skipped}")

    # Build name index
    by_name = defaultdict(list)
    for p in clean_products:
        by_name[normalize(p['reg_name'])].append(p)
    print(f"  ✓ 名称索引: {len(by_name)} 个药品名")

    # Step 3: Match products to drugs
    print("\n[3/3] 匹配产品到药品...")
    matched_drugs = 0
    total_variants = 0

    for drug in drugs:
        drug_norm = normalize(drug['name'])
        if not drug_norm or len(drug_norm) < 2:
            continue

        variants = []
        seen_codes = set()

        # Strategy 1: Exact normalized name match
        if drug_norm in by_name:
            for p in by_name[drug_norm]:
                c = p['code']
                if c not in seen_codes:
                    seen_codes.add(c)
                    variants.append(p)

        # Strategy 2: Drug name contained in PDF name OR PDF name contained in drug name
        if not variants:
            for pdf_norm, prods in by_name.items():
                if len(variants) >= 300: break
                if drug_norm in pdf_norm or pdf_norm in drug_norm:
                    for p in prods:
                        c = p['code']
                        if c not in seen_codes:
                            seen_codes.add(c)
                            variants.append(p)

        # Strategy 3: Also try bracketed alternatives
        if not variants:
            # Extract text in brackets: "埃索美拉唑(艾司奥美拉唑)" → both parts
            bracket_matches = re.findall(r'([^(]+)\(([^)]+)\)', drug_norm)
            for main, alt in bracket_matches:
                main_n = normalize(main)
                alt_n = normalize(alt)
                for try_name in [main_n, alt_n, drug_norm.replace('('+alt+')','')]:
                    if not try_name: continue
                    for pdf_norm, prods in by_name.items():
                        if len(variants) >= 300: break
                        if try_name == pdf_norm or try_name in pdf_norm or pdf_norm in try_name:
                            for p in prods:
                                c = p['code']
                                if c not in seen_codes:
                                    seen_codes.add(c)
                                    variants.append(p)

        if variants:
            drug['variants'] = variants[:500]  # limit per drug
            total_variants += len(drug['variants'])
            matched_drugs += 1

    print(f"  ✓ 有产品数据的药品: {matched_drugs}/{len(drugs)}")
    print(f"  ✓ 总产品明细: {total_variants}")

    # Step 4: Save
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)

    gz_path = OUTPUT + '.gz'
    with open(OUTPUT, 'rb') as f_in:
        with gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    size = os.path.getsize(OUTPUT)
    gzsize = os.path.getsize(gz_path)
    print(f"\n  ✓ drugs.json: {size/1024/1024:.1f} MB")
    print(f"  ✓ drugs.json.gz: {gzsize/1024/1024:.1f} MB")

    # Also save clean products as detail
    detail_path = os.path.join(BASE, 'drugs_detail.json')
    with open(detail_path, 'w', encoding='utf-8') as f:
        json.dump(clean_products, f, ensure_ascii=False, indent=1)
    with open(detail_path, 'rb') as f_in:
        with gzip.open(detail_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    print("\n" + "=" * 60)
    print("✅ 重建完成!")
    print("=" * 60)

if __name__ == '__main__':
    main()
