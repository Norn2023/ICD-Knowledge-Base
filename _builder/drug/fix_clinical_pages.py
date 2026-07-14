"""
Fix clinical_ref_index.json page numbers by searching PDF content directly.
The TOC-extracted page numbers have inconsistent offsets vs physical PDF pages.
"""
import fitz, json, sys, os, gzip, time, re

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def find_file(keyword):
    for f in os.listdir(BASE):
        if keyword in f and f.endswith('.pdf'):
            return os.path.join(BASE, f)
    return None

def main():
    print("=" * 50)
    print("修正临床用药须知页面偏移")
    print("=" * 50)

    # Load index
    idx_path = os.path.join(BASE, 'clinical_ref_index.json')
    with open(idx_path, 'r', encoding='utf-8') as f:
        idx = json.load(f)

    chem = idx.get('chem', [])
    print(f"临床化学药卷: {len(chem)} 条目")

    # Open PDF
    pdf_path = find_file('化学药')
    if not pdf_path:
        print("未找到化学药卷PDF")
        return

    doc = fitz.open(pdf_path)
    total = doc.page_count
    print(f"PDF: {total} 页")

    # For each entry, search for the drug name in the PDF to find the correct page
    # Strategy: search around the TOC page + common offsets, take the first match
    corrected = 0
    not_found = 0

    t0 = time.time()
    for i, entry in enumerate(chem):
        name = entry.get('name', '')
        toc_page = entry.get('page', 1)
        if not name or toc_page < 1:
            continue

        # Search range: TOC page ± offset range
        # Typical offset is +42 (front matter), but varies
        search_start = max(0, toc_page + 30)
        search_end = min(total, toc_page + 60)

        found_page = None
        for p in range(search_start, search_end):
            t = doc[p].get_text()
            if name in t:
                found_page = p + 1  # 1-based
                break

        if found_page:
            if found_page != toc_page:
                entry['page'] = found_page
                corrected += 1
        else:
            # Try wider search
            for p in range(max(0, toc_page), min(total, toc_page + 80)):
                t = doc[p].get_text()
                if name in t:
                    found_page = p + 1
                    break
            if found_page and found_page != toc_page:
                entry['page'] = found_page
                corrected += 1
            elif not found_page:
                not_found += 1

        if (i + 1) % 500 == 0:
            elapsed = time.time() - t0
            print(f"  {i+1}/{len(chem)} ({elapsed:.0f}s) corrected={corrected} missing={not_found}...")

    doc.close()
    elapsed = time.time() - t0
    print(f"  Done: corrected={corrected} missing={not_found} ({elapsed:.0f}s)")

    # Save corrected index
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    with open(idx_path, 'rb') as f_in:
        with gzip.open(idx_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    print(f"\n✅ 已保存 corrected clinical_ref_index.json")

    # Show some corrections
    print("\n修正样例:")
    count = 0
    for e in chem:
        if count >= 10: break
        name = e.get('name', '')
        page = e.get('page', 0)
        if name and page:
            print(f"  {name} → 第{page}页")
            count += 1

if __name__ == '__main__':
    main()
