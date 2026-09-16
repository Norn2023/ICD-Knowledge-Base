"""
Rebuild drugs.json with ALL 14 fields from pdf_products.json
Matching strategy: code -> name -> manufacturer+spec
Replaces drug variants with full PDF product data
"""
import json, sys, gzip, os, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))

def normalize(s):
    """Normalize string for matching: lowercase, remove spaces and special chars"""
    if not s: return ''
    return re.sub(r'[\s　（）()]+', '', str(s)).lower()

def clean_repeated(s):
    """Fix PDF merged-cell artifacts: repeated substrings"""
    if not s or len(s) < 8:
        return s
    # Strategy 1: exact repetition
    max_unit = len(s) // 2
    for unit_len in range(2, min(max_unit, 50) + 1):
        if len(s) % unit_len == 0:
            unit = s[:unit_len]
            if s == unit * (len(s) // unit_len):
                return unit
    # Strategy 2: mid-split (first half == second half)
    mid = len(s) // 2
    if s[:mid] == s[mid:2*mid]:
        return s[:mid]
    # Strategy 3: sliding-window repeated substring (skip variable prefix)
    for unit_len in range(2, min(40, len(s)//3 + 1)):
        for start in range(0, min(unit_len, 20)):
            if start + unit_len > len(s):
                continue
            unit = s[start:start+unit_len]
            count = 1
            pos = start + unit_len
            while pos + unit_len <= len(s):
                if s[pos:pos+unit_len] == unit:
                    count += 1
                    pos += unit_len
                else:
                    break
            if count >= 3 and pos >= len(s) * 0.6:
                return s[:start] + unit
    # Strategy 4: truncate very long strings to a reasonable length
    if len(s) > 200:
        return s[:200] + '…'
    return s

def clean_pdf_product(p):
    """Clean one PDF product record to consistent field names"""
    return {
        'code': str(p.get('药品代码', '')).strip(),
        'reg_name': clean_repeated(str(p.get('注册名称', '')).strip()),
        'reg_form': clean_repeated(str(p.get('注册剂型', '')).strip()),
        'reg_spec': clean_repeated(str(p.get('注册规格', '')).strip()),
        'trade_name': clean_repeated(str(p.get('商品名称', '')).strip()),
        'dosage_form': clean_repeated(str(p.get('剂型', '')).strip()),
        'spec': clean_repeated(str(p.get('规格', '')).strip()),
        'pack_material': clean_repeated(str(p.get('包装材质', '')).strip()),
        'pack_qty': str(p.get('最小包装数量', '')).strip(),
        'unit_prep': str(p.get('最小制剂单位', '')).strip(),
        'unit_pack': str(p.get('最小包装单位', '')).strip(),
        'manufacturer': clean_repeated(str(p.get('药品企业', '')).strip()),
        'approval': clean_repeated(str(p.get('批准文号', '')).strip()),
        'barcode': str(p.get('药品本位码', '')).strip(),
    }

def variant_key(v):
    """Create a key for deduplication using code+barcode or name+mfr+spec"""
    code = v.get('code', '')
    bc = v.get('barcode', '')
    if code:
        return ('code', code)
    if bc:
        return ('bc', bc)
    # Fallback: name + manufacturer + spec
    name = normalize(v.get('reg_name', '') or v.get('name', ''))
    mfr = normalize(v.get('manufacturer', ''))
    sp = normalize(v.get('spec', ''))
    return ('nm', f'{name}|{mfr}|{sp}')

def main():
    print("=" * 60)
    print("药品数据重建 - 名称匹配 + 全部14个PDF字段")
    print("=" * 60)

    # 1. Load PDF products
    print("\n[1/5] 加载 PDF 产品数据...")
    pdf_path = os.path.join(BASE, 'pdf_products.json')
    with open(pdf_path, 'r', encoding='utf-8') as f:
        pdf_products = json.load(f)
    print(f"  ✓ {len(pdf_products)} 条原始PDF记录")

    # Filter + clean
    header_texts = {'药品代码', '注册名称', '注册剂型'}
    clean_products = []
    for p in pdf_products:
        code = p.get('药品代码', '')
        if not code or code in header_texts:
            continue
        clean_products.append(clean_pdf_product(p))
    print(f"  ✓ 清理后 {len(clean_products)} 条有效产品")

    # 2. Build lookup indices
    print("\n[2/5] 构建索引...")
    by_code = {}
    by_name = defaultdict(list)
    for p in clean_products:
        # Code index
        code = p['code']
        if code and code not in by_code:
            by_code[code] = p
        # Name index (normalized)
        name = normalize(p['reg_name'])
        if name:
            by_name[name].append(p)

    print(f"  ✓ 代码索引: {len(by_code)} 个")
    print(f"  ✓ 名称索引: {len(by_name)} 个药品名")

    # 3. Load current drugs.json
    print("\n[3/5] 加载 drugs.json...")
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    print(f"  ✓ {len(drugs)} 条药品目录")

    # 4. Build substring index for fuzzy matching
    print("\n[4/6] 构建模糊匹配索引...")
    # Store PDF names in a list for substring scanning
    pdf_name_list = list(by_name.keys())  # normalized names -> list of products
    pdf_len = len(pdf_name_list)
    print(f"  ✓ {pdf_len} 个PDF药品名可用于模糊匹配")

    # 5. Match and rebuild
    print("\n[5/6] 匹配并重建...")
    stats = {'code_match': 0, 'name_match': 0, 'fuzzy_match': 0, 'unmatched': 0, 'added_from_pdf': 0}
    total_old_variants = 0
    total_new_variants = 0

    def find_pdf_by_name(name_str):
        """Try to find PDF products by name: exact -> substring -> stripped"""
        if not name_str:
            return []
        nn = normalize(name_str)
        if not nn or len(nn) < 2:
            return []

        # Exact match
        if nn in by_name and by_name[nn]:
            return by_name[nn]

        # Substring: catalog name is part of PDF name
        candidates = []
        for pdf_norm, prods in by_name.items():
            if nn in pdf_norm or pdf_norm in nn:
                candidates.extend(prods)
        if candidates:
            return candidates

        # Try removing common suffixes
        for suffix in ['片', '胶囊', '注射液', '颗粒', '口服液', '滴丸', '软膏', '乳膏', '栓', '散',
                       '丸', '糖浆', '混悬液', '气雾剂', '喷雾剂', '贴剂', '凝胶', '洗剂', '搽剂',
                       '滴眼液', '滴耳液', '滴鼻液', '软胶囊', '缓释片', '缓释胶囊', '肠溶片', '肠溶胶囊',
                       '溶液', '粉针', '水针', '冻干']:
            if nn.endswith(suffix):
                stem = nn[:-len(suffix)]
                if len(stem) >= 2:
                    for pdf_norm, prods in by_name.items():
                        if stem in pdf_norm or pdf_norm in stem:
                            candidates.extend(prods)
        return candidates

    def find_best_pdf_match(variant):
        """Find best PDF product match for a variant"""
        # 1. Try code
        code = variant.get('code', '')
        if code and code in by_code:
            return by_code[code], 'code_match'

        # 2. Try name (using variant's old name or reg_name)
        vname = variant.get('name', '') or variant.get('reg_name', '')
        candidates = find_pdf_by_name(vname)
        if candidates:
            # Prefer manufacturer match
            mfr_norm = normalize(variant.get('manufacturer', ''))
            for c in candidates:
                if mfr_norm and normalize(c['manufacturer']) == mfr_norm:
                    return c, 'name_match'
            return candidates[0], 'name_match'

        return None, None

    for drug in drugs:
        old_variants = drug.get('variants', [])
        total_old_variants += len(old_variants)

        new_variants = []
        seen_keys = set()

        for v in old_variants:
            full, match_type = find_best_pdf_match(v)

            if full:
                new_variants.append(full)
                seen_keys.add(variant_key(full))
                stats[match_type] += 1
            else:
                # Keep old data with all fields
                new_variants.append({
                    'code': v.get('code', ''),
                    'reg_name': v.get('name', '') or v.get('reg_name', ''),
                    'reg_form': '',
                    'reg_spec': '',
                    'trade_name': '',
                    'dosage_form': v.get('form', ''),
                    'spec': v.get('spec', ''),
                    'pack_material': '',
                    'pack_qty': '',
                    'unit_prep': '',
                    'unit_pack': '',
                    'manufacturer': v.get('manufacturer', ''),
                    'approval': v.get('approval', ''),
                    'barcode': v.get('barcode', ''),
                })
                stats['unmatched'] += 1

        # Also add PDF products closely matching this drug's catalog name
        drug_name = drug.get('name', '')
        drug_norm = normalize(drug_name)
        if drug_norm and len(drug_norm) >= 2:
            # Only add PDF products whose name is a close match to the drug catalog name
            close_matches = []
            for pdf_norm, prods in by_name.items():
                if len(close_matches) >= 300:  # limit per drug
                    break
                # Criteria: exact match, prefix match, or drug name fully contained
                if pdf_norm == drug_norm:
                    close_matches.extend(prods)
                elif pdf_norm.startswith(drug_norm):
                    # Check remaining part is a common suffix
                    remainder = pdf_norm[len(drug_norm):]
                    common_suffixes = ['片', '胶囊', '注射液', '注射用', '颗粒', '口服液', '滴丸',
                                      '软膏', '乳膏', '栓', '散', '丸', '糖浆', '混悬液', '气雾剂',
                                      '喷雾剂', '贴剂', '凝胶', '洗剂', '搽剂', '滴眼液', '滴耳液',
                                      '滴鼻液', '软胶囊', '缓释片', '缓释胶囊', '肠溶片', '肠溶胶囊',
                                      '溶液', '粉针', '水针', '冻干', '粉针剂', '乳胶剂', '乳剂',
                                      '眼膏', '眼用凝胶', '滴剂', '酊剂', '膜剂', '栓剂', '颗粒剂',
                                      '干混悬剂', '泡腾片', '分散片', '口崩片', '咀嚼片', '含片',
                                      '舌下片', '植入剂', '贴片', '巴布剂', '煎膏剂', '合剂',
                                      '口服溶液', '口服混悬液', '糖浆剂', '酒剂', '酊剂', '醑剂',
                                      '涂剂', '涂膜剂', '搽剂', '灌肠剂', '灌洗剂', '冲洗剂',
                                      '注射用无菌粉末', '注射用浓溶液']
                    for suf in common_suffixes:
                        if remainder == normalize(suf):
                            close_matches.extend(prods)
                            break
                elif len(drug_norm) >= 3 and drug_norm in pdf_norm:
                    # Drug name contained in PDF name - but only if drug name is significant
                    close_matches.extend(prods)

            for p in close_matches[:500]:  # max per drug
                key = variant_key(p)
                if key not in seen_keys:
                    new_variants.append(p)
                    seen_keys.add(key)
                    stats['added_from_pdf'] += 1

        # Limit total variants per drug to prevent extreme cases
        if len(new_variants) > 500:
            new_variants = new_variants[:500]

        drug['variants'] = new_variants
        total_new_variants += len(new_variants)

    print(f"  ✓ 原 variants: {total_old_variants}")
    print(f"  ✓ 代码匹配: {stats['code_match']} ({stats['code_match']/max(total_old_variants,1)*100:.1f}%)")
    print(f"  ✓ 名称匹配: {stats['name_match']} ({stats['name_match']/max(total_old_variants,1)*100:.1f}%)")
    print(f"  ✓ 未匹配: {stats['unmatched']} ({stats['unmatched']/max(total_old_variants,1)*100:.1f}%)")
    print(f"  ✓ PDF新增: {stats['added_from_pdf']}")
    print(f"  ✓ 新 variants: {total_new_variants}")

    # 6. Save
    print("\n[6/6] 保存...")
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)

    drugs_gz_path = drugs_path + '.gz'
    with open(drugs_path, 'rb') as f_in:
        with gzip.open(drugs_gz_path, 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    drugs_size = os.path.getsize(drugs_path)
    dgz_size = os.path.getsize(drugs_gz_path)
    print(f"  ✓ drugs.json: {drugs_size/1024/1024:.1f} MB")
    print(f"  ✓ drugs.json.gz: {dgz_size/1024/1024:.1f} MB")

    # Also save drugs_detail.json (flat list for reference)
    detail_path = os.path.join(BASE, 'drugs_detail.json')
    with open(detail_path, 'w', encoding='utf-8') as f:
        json.dump(clean_products, f, ensure_ascii=False, indent=1)
    with open(detail_path, 'rb') as f_in:
        with gzip.open(detail_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    print("\n" + "=" * 60)
    print("✅ 重建完成!")
    drugs_with_variants = sum(1 for d in drugs if d.get('variants'))
    print(f"  {drugs_with_variants}/{len(drugs)} 药品有产品数据")
    print("=" * 60)

if __name__ == '__main__':
    main()
