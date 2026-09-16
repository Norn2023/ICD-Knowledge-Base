"""
Extract drug name indices from clinical reference PDFs:
- 临床用药须知 (化学药卷)
- 中国国家处方集
"""
import fitz, json, sys, os, re, gzip

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def find_file(keyword):
    """Find a file in the current directory containing keyword"""
    for f in os.listdir(BASE):
        if keyword in f and f.endswith('.pdf'):
            return os.path.join(BASE, f)
    return None

def extract_toc_entries(doc, start_page=10, end_page=50):
    """Extract drug name → page entries from TOC pages"""
    entries = []
    for pg in range(start_page, min(end_page, doc.page_count)):
        text = doc[pg].get_text()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Pattern: drug name followed by dots/spaces then page number
            # e.g., "枸橼酸舒芬太尼⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯177"
            m = re.match(r'^([一-鿿（）()\w·]+)[\s⋯…\.]+(\d+)\s*$', line)
            if m:
                name = m.group(1).strip()
                page = int(m.group(2))
                if len(name) >= 2 and len(name) <= 30:
                    entries.append({'name': name, 'page': page})
    return entries

def extract_prescription_toc(doc, start_page=10, end_page=50):
    """Extract section entries from 处方集 TOC (disease-based)"""
    entries = []
    for pg in range(start_page, min(end_page, doc.page_count)):
        text = doc[pg].get_text()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Pattern: chapter/section name with page number
            m = re.match(r'^.{2,40}[\s⋯…\.]+(\d+)\s*$', line)
            if m and any('一' <= c <= '鿿' for c in line):
                page = int(m.group(1))
                name = re.sub(r'[\s⋯…\.\d]+$', '', line).strip()
                if 2 <= len(name) <= 40:
                    entries.append({'name': name, 'page': page})
    return entries

def main():
    print("=" * 60)
    print("提取临床用药须知 & 处方集索引")
    print("=" * 60)

    all_data = {}

    # 1. 化学药卷
    chem_file = find_file('化学药')
    if chem_file:
        print(f"\n[化学药卷] {os.path.basename(chem_file)}")
        doc = fitz.open(chem_file)
        print(f"  {doc.page_count} 页")

        # Search for TOC pages (look for "目录" keyword)
        toc_start = None
        for pg in range(5, 30):
            text = doc[pg].get_text()
            if '目录' in text or '目 录' in text:
                toc_start = pg
                print(f"  目录从第 {pg+1} 页开始")
                break

        if toc_start:
            # Extract TOC from the next ~30 pages
            entries = []
            for pg in range(toc_start, min(toc_start + 50, doc.page_count)):
                text = doc[pg].get_text()
                # Skip pure page number lines
                for line in text.split('\n'):
                    line = line.strip()
                    if not line: continue
                    # Drug name + dots + page number
                    m = re.match(r'^([一-鿿（）()\w\-·ⅡⅢⅣⅤⅠⅥⅦⅧⅨⅩ]+)[⋯…\.\s]{2,}(\d+)\s*$', line)
                    if m:
                        name = m.group(1).strip()
                        page = int(m.group(2))
                        if 2 <= len(name) <= 40 and name not in ('目录','目 录','前言','附录'):
                            entries.append({'name': name, 'page': page})

            # Deduplicate
            seen = set()
            unique = []
            for e in entries:
                if e['name'] not in seen:
                    seen.add(e['name'])
                    unique.append(e)

            print(f"  提取 {len(unique)} 个药物词条")
            all_data['chem'] = unique

        doc.close()

    # 2. 处方集 - extract chapter-level TOC
    rx_file = find_file('处方集')
    if rx_file:
        print(f"\n[处方集] {os.path.basename(rx_file)}")
        doc = fitz.open(rx_file)
        print(f"  {doc.page_count} 页")

        # TOC is around pages 11-12, format: "第X章 疾病名/ 页码"
        chapters = []
        for pg in range(8, 18):
            text = doc[pg].get_text()
            for line in text.split('\n'):
                line = line.strip()
                # Format: "第1 章神经系统疾病与用药/ 23" or "第X章 .../ N"
                m = re.match(r'^(第\s*[\d一二三四五六七八九十]+\s*章\s*.+?)\s*/\s*(\d+)\s*$', line)
                if m:
                    name = re.sub(r'\s+', '', m.group(1))
                    chapters.append({'name': name, 'page': int(m.group(2))})
                else:
                    # Try section format: "一、临床用药管理相关法规介绍/ 3"
                    m = re.match(r'^([一二三四五六七八九十]+[、，,]\s*.+?)\s*/\s*(\d+)\s*$', line)
                    if m:
                        name = re.sub(r'\s+', '', m.group(1))
                        chapters.append({'name': name, 'page': int(m.group(2))})

        # Also scan for detailed drug TOC within each chapter
        # Look at chapter start pages (around p23, p83, p130, etc.)
        for ch_page in [23, 83, 130, 180, 230, 280, 330, 380, 430, 480, 530, 580, 630, 680, 730, 780, 830, 880, 930, 980, 1030]:
            if ch_page < doc.page_count:
                text = doc[ch_page].get_text()[:500]
                # Check if this is a chapter start
                for line in text.split('\n'):
                    line = line.strip()
                    m = re.match(r'^(第\s*[\d一二三四五六七八九十]+\s*章\s*.+?)\s*/\s*(\d+)\s*$', line)
                    if m:
                        name = re.sub(r'\s+', '', m.group(1))
                        if name not in [c['name'] for c in chapters]:
                            chapters.append({'name': name, 'page': int(m.group(2))})

        # Dedup
        seen = set()
        unique = []
        for e in chapters:
            if e['name'] not in seen:
                seen.add(e['name'])
                unique.append(e)

        print(f"  提取 {len(unique)} 个章节词条")
        all_data['rx'] = unique
        doc.close()

    # Save
    out_path = os.path.join(BASE, 'clinical_ref_index.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=1)

    with open(out_path, 'rb') as f_in:
        with gzip.open(out_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    total = sum(len(v) for v in all_data.values())
    print(f"\n✅ 总计 {total} 条索引")
    print(f"   clinical_ref_index.json.gz: {os.path.getsize(out_path+'.gz')/1024:.0f} KB")

    # Sample
    for key in all_data:
        print(f"\n  {key} 样例:")
        for e in all_data[key][:5]:
            print(f"    {e['name']} → 第{e['page']}页")

if __name__ == '__main__':
    main()
