"""
Build comprehensive drug index for 中国国家处方集（第2版，2020）.
Searches the full PDF for every drug from drugs.json and records page numbers.
"""
import fitz, json, sys, os, gzip, time, re

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def normalize(s):
    """Normalize drug name for matching: remove spaces, parens, special chars"""
    if not s: return ''
    s = re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤ]+', '', str(s))
    return s

# Common OCR character errors in this specific PDF
# The OCR engine fails to recognize certain characters, replacing them with lookalikes
OCR_VARIANTS = {
    '胍': ['肌', '腿', '版', 'J肌', 'j肌'],
    '唑': ['唾', '哩', '哇', '峰', '哇'],
    '脲': ['脉', '尿', '睬'],
    '胰': ['膜', '姨'],
    '酮': ['酣', '嗣', '嗣'],
    '酚': ['盼', '酣', '醋'],
    '孢': ['抱', '胞'],
    '呋': ['味', '哄'],
    '酰': ['酷'],
    '脒': ['眯'],
    '嗪': ['嗦', '嚷'],
    '哌': ['呱', '趴'],
}

def make_ocr_variants(name):
    """Generate OCR-garbled variants including multi-character substitutions (up to 2)"""
    variants = set()
    variants.add(name)  # original

    # Find all OCR-prone character positions
    ocr_positions = []
    for i, c in enumerate(name):
        if c in OCR_VARIANTS:
            ocr_positions.append((i, c))

    if not ocr_positions:
        return [name]

    # Single substitutions
    for pos, orig_char in ocr_positions:
        for sub in OCR_VARIANTS[orig_char]:
            var = name[:pos] + sub + name[pos+1:]
            variants.add(var)

    # Double substitutions (for 2+ OCR-prone chars) - limit to first 4 positions to avoid explosion
    if len(ocr_positions) >= 2:
        limited = ocr_positions[:4]  # cap to avoid combinatorial explosion
        for i in range(len(limited)):
            for j in range(i+1, len(limited)):
                pos1, c1 = limited[i]
                pos2, c2 = limited[j]
                for sub1 in OCR_VARIANTS[c1][:3]:  # limit alternatives per char
                    for sub2 in OCR_VARIANTS[c2][:3]:
                        chars = list(name)
                        chars[pos1] = sub1
                        chars[pos2] = sub2
                        variants.add(''.join(chars))
                if len(variants) > 120:  # safety cap
                    break
            if len(variants) > 120:
                break

    return list(variants)[:150]  # hard cap

def main():
    print("=" * 60)
    print("构建 中国国家处方集 药物索引")
    print("=" * 60)

    # Load drug names
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    print(f"药品目录: {len(drugs)} 个药物")

    # Build drug name lookup: normalized_name → [drug_entries]
    # Also collect shorter sub-names for matching
    drug_names = []  # [(normalized, original, drug_obj)]
    for d in drugs:
        name = d.get('name', '').strip()
        if not name or len(name) < 2:
            continue
        norm = normalize(name)
        if len(norm) >= 3:
            drug_names.append((norm, name, d))

    print(f"有效药名: {len(drug_names)} 个")

    # Open PDF
    pdf_path = None
    for f in os.listdir(BASE):
        if '处方集' in f and 'OCR' in f and f.endswith('.pdf'):
            pdf_path = os.path.join(BASE, f)
            break
    if not pdf_path:
        print("未找到处方集PDF")
        return

    doc = fitz.open(pdf_path)
    total = doc.page_count
    print(f"PDF: {total} 页")

    # Build index: page by page, checking all drugs
    # drug → set of pages
    drug_pages = {}  # normalized_name → set(pages)

    # Sort drug names by length descending for faster early exit
    drug_names.sort(key=lambda x: -len(x[0]))

    t0 = time.time()
    skipped_pages = 0

    for page_idx in range(total):
        pageno = page_idx + 1
        t = doc[page_idx].get_text()

        if len(t.strip()) < 50:  # Skip nearly-empty pages
            skipped_pages += 1
            continue

        # For each drug, check if name or OCR variant appears on this page
        for norm_name, orig_name, drug in drug_names:
            if norm_name in drug_pages and len(drug_pages[norm_name]) >= 5:
                continue  # Already have enough matches

            # Try exact match first
            if norm_name in t:
                if norm_name not in drug_pages:
                    drug_pages[norm_name] = set()
                drug_pages[norm_name].add(pageno)
                continue

            # Try OCR variants (only for names with OCR-prone chars)
            has_ocr_char = any(c in norm_name for c in OCR_VARIANTS)
            if has_ocr_char:
                for variant in make_ocr_variants(norm_name):
                    if variant != norm_name and variant in t:
                        if norm_name not in drug_pages:
                            drug_pages[norm_name] = set()
                        drug_pages[norm_name].add(pageno)
                        break

        # Progress
        if pageno % 100 == 0:
            elapsed = time.time() - t0
            found_count = len(drug_pages)
            print(f"  第{pageno}页 ({elapsed:.0f}s) 已匹配{found_count}个药物...")

    doc.close()
    elapsed = time.time() - t0

    # Stats
    total_matches = sum(len(p) for p in drug_pages.values())
    print(f"\n  完成: {elapsed:.0f}s")
    print(f"  匹配药物: {len(drug_pages)}/{len(drug_names)}")
    print(f"  总匹配次数: {total_matches}")
    print(f"  跳过空页: {skipped_pages}")

    # Build index entries for clinical_ref_index.json rx section
    rx_entries = []
    for norm_name, orig_name, drug in drug_names:
        if norm_name in drug_pages:
            for page in sorted(drug_pages[norm_name])[:5]:  # Max 5 pages per drug
                rx_entries.append({
                    'name': orig_name,
                    'page': page,
                    'file': '中国国家处方集（第2版，2020）OCR.pdf',
                    'fid': 'rx'
                })

    # Sort by name then page
    rx_entries.sort(key=lambda x: (x['name'], x['page']))

    print(f"\n索引条目: {len(rx_entries)}")

    # Update clinical_ref_index.json
    clin_path = os.path.join(BASE, 'clinical_ref_index.json')
    with open(clin_path, 'r', encoding='utf-8') as f:
        clin = json.load(f)

    # Keep existing TOC entries (pages < 22) and merge with new drug entries
    old_rx = clin.get('rx', [])
    toc_entries = [e for e in old_rx if e.get('page', 0) < 22]
    print(f"  保留目录条目: {len(toc_entries)}")

    clin['rx'] = rx_entries + toc_entries
    # Remove duplicates (same name + page)
    seen = set()
    unique = []
    for e in clin['rx']:
        key = (e.get('name', ''), e.get('page', 0))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    clin['rx'] = unique
    clin['rx'].sort(key=lambda x: (x.get('name', ''), x.get('page', 0)))

    print(f"  最终处方集条目: {len(clin['rx'])}")

    with open(clin_path, 'w', encoding='utf-8') as f:
        json.dump(clin, f, ensure_ascii=False, indent=1)
    with open(clin_path, 'rb') as f_in:
        with gzip.open(clin_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    print(f"\n✅ 已保存 clinical_ref_index.json")

    # Show sample entries
    print("\n处方集收录样例:")
    samples = [e for e in rx_entries if e['name'] in ['盐酸二甲双胍', '阿莫西林', '奥美拉唑', '阿托伐他汀', '氨氯地平', '布洛芬', '对乙酰氨基酚']]
    for e in samples[:15]:
        print(f"  {e['name']} → 第{e['page']}页")

    # Show page distribution
    drugs_with_multi = sum(1 for v in drug_pages.values() if len(v) > 1)
    print(f"\n出现在多个页面的药物: {drugs_with_multi}")

if __name__ == '__main__':
    main()
