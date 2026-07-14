"""
Re-index clinical reference (chem) to only match drug names at HEADING-level font size.
This filters out matches where the drug name appears in body text paragraphs.
"""
import fitz, json, sys, os, gzip, time, re

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 60)
    print("重新索引 临床用药须知 — 仅匹配标题级药名")
    print("=" * 60)

    # Load drug names
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    drug_names = []
    for d in drugs:
        name = d.get('name', '').strip()
        if not name or len(name) < 3:
            continue
        norm = re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤ]+', '', str(name))
        if len(norm) >= 3:
            drug_names.append((norm, name))

    drug_names.sort(key=lambda x: -len(x[0]))
    print(f"药品: {len(drug_names)} 个")

    # Find chemical reference PDF
    pdf_path = None
    for f in os.listdir(BASE):
        if '化学药' in f and '中药' not in f and f.endswith('.pdf'):
            pdf_path = os.path.join(BASE, f)
            break
    if not pdf_path:
        print("未找到化学药卷PDF")
        return

    doc = fitz.open(pdf_path)
    total = doc.page_count
    print(f"PDF: {total} 页")

    # Build heading-level index
    drug_pages = {}  # norm_name → [(page, font_size)]
    t0 = time.time()

    for page_idx in range(total):
        pageno = page_idx + 1
        blocks = doc[page_idx].get_text('dict')['blocks']

        # Analyze font distribution on this page
        fonts = []  # list of (size, text)
        for b in blocks:
            if 'lines' not in b:
                continue
            for l in b['lines']:
                for s in l['spans']:
                    text = s['text'].strip()
                    if text and len(text) >= 2:
                        fonts.append((s['size'], text, s.get('flags', 0)))

        if not fonts:
            continue

        # Find the heading font size threshold
        # Strategy: the top 25% largest text is considered "heading level"
        sizes = sorted(set(f[0] for f in fonts), reverse=True)
        if not sizes:
            continue

        # Threshold: 85th percentile of font sizes, but at least 10pt
        size_threshold_idx = max(0, int(len(sizes) * 0.25))
        heading_threshold = sizes[size_threshold_idx] if size_threshold_idx < len(sizes) else sizes[-1]
        # Also accept anything >= 10.5pt as heading-level (drug names are typically 10.5-13pt)
        heading_threshold = max(heading_threshold, 10.3)

        # For pages with very uniform text (all within 1pt), lower threshold
        if sizes[0] - sizes[-1] < 1.5:
            heading_threshold = sizes[0] - 0.5  # top of the range

        # Check each drug name against heading-level spans on this page
        for norm_name, orig_name in drug_names:
            if norm_name in drug_pages and len(drug_pages[norm_name]) >= 3:
                continue

            for size, text, flags in fonts:
                if size < heading_threshold:
                    continue
                if norm_name in text:
                    if norm_name not in drug_pages:
                        drug_pages[norm_name] = []
                    # Record with font size for ranking
                    drug_pages[norm_name].append((pageno, round(size, 1)))
                    break  # one match per page per drug

        if pageno % 200 == 0:
            elapsed = time.time() - t0
            print(f"  {pageno}/{total} ({elapsed:.0f}s) matched {len(drug_pages)} drugs...")

    doc.close()
    elapsed = time.time() - t0
    print(f"  Done: {elapsed:.0f}s, {len(drug_pages)} drugs matched")

    # Build chem entries sorted by name
    chem_entries = []
    for norm_name, orig_name in drug_names:
        if norm_name in drug_pages:
            pages = drug_pages[norm_name]
            # Sort by font size descending (best heading matches first), then by page
            pages.sort(key=lambda x: (-x[1], x[0]))
            for page, font_size in pages[:3]:  # max 3 pages
                chem_entries.append({
                    'name': orig_name,
                    'page': page,
                    'file': os.path.basename(pdf_path),
                    'fid': 'chem',
                    'font_pt': font_size  # for debugging
                })

    # Sort by name then page
    chem_entries.sort(key=lambda x: (x['name'], x['page']))
    print(f"  Chem entries: {len(chem_entries)}")

    # Update clinical_ref_index.json
    clin_path = os.path.join(BASE, 'clinical_ref_index.json')
    with open(clin_path, 'r', encoding='utf-8') as f:
        clin = json.load(f)

    clin['chem'] = chem_entries

    with open(clin_path, 'w', encoding='utf-8') as f:
        json.dump(clin, f, ensure_ascii=False, indent=1)
    with open(clin_path, 'rb') as f_in:
        with gzip.open(clin_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    print(f"\n✅ Updated clinical_ref_index.json (chem={len(chem_entries)}, rx={len(clin.get('rx',[]))})")

    # Show sample
    print("\n样例 (标题级匹配):")
    samples = ['地西泮', '阿莫西林', '奥美拉唑', '阿托伐他汀', '氨氯地平', '布洛芬', '二甲双胍']
    for name in samples:
        matches = [e for e in chem_entries if e['name'] == name]
        if matches:
            info = ', '.join(f"p{p['page']}({p.get('font_pt','?')}pt)" for p in matches[:3])
            print(f"  {name}: {info}")
        else:
            print(f"  {name}: NOT FOUND")

if __name__ == '__main__':
    main()
