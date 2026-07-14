"""
Pre-extract text from pharmacopoeia and clinical reference PDFs.
Outputs page_cache.json.gz: flat dict {fid}|{page} → text
Server uses this cache in /page_text endpoint for instant preview.
"""
import fitz, json, sys, os, gzip, time, re

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

# ── Chinese PDF text reformatter ──
# Patterns for noise removal
_RE_PAGE_NUM = re.compile(r'^\s*\d{1,4}\s*$')
_RE_HEADER = re.compile(r'^(中国药典\d{4}年版|中华人民共和国药典.*|临床用药须知.*)$')
_RE_SECTION = re.compile(r'^[【〔［\[]')
_RE_CHAPTER = re.compile(r'^第[一二三四五六七八九十百千\d]+[章节篇]')
# Sentence-ending punctuation (Chinese + Western)
_SENTENCE_END = set('。！？…）】」』》)')
_CLAUSE_END = set('，、；：·—…')

def _is_ascii_line(line):
    """Line is mostly ASCII (pinyin/English/Latin name)"""
    ascii_count = sum(1 for c in line if ord(c) < 128)
    return ascii_count > len(line) * 0.6

def reformat_text(raw_text):
    """Smart reformat: merge mid-sentence breaks, keep structure."""
    lines = [l.strip() for l in raw_text.split('\n')]
    lines = [l for l in lines if l]  # remove blank lines

    if not lines:
        return raw_text

    # Phase 1: Filter noise lines
    cleaned = []
    for line in lines:
        # Skip standalone page numbers
        if _RE_PAGE_NUM.match(line) and len(line) <= 4:
            continue
        # Skip repeating headers
        if _RE_HEADER.match(line):
            continue
        # Skip header fragments
        if line in ('2025年版', '2020年版'):
            continue
        cleaned.append(line)

    if not cleaned:
        return raw_text

    # Phase 2: Merge mid-sentence breaks
    merged = []
    buf = ''
    for line in cleaned:
        # Section/chapter headers → standalone
        if _RE_SECTION.match(line) or _RE_CHAPTER.match(line):
            if buf:
                merged.append(buf)
                buf = ''
            merged.append(line)
            continue

        # Very short lines (<5 CJK chars) → likely standalone (title, tag)
        cjk_count = sum(1 for c in line if '一' <= c <= '鿿')
        if len(line) <= 8 and cjk_count <= 4:
            if buf:
                merged.append(buf)
                buf = ''
            merged.append(line)
            continue

        # ASCII-dominant lines → standalone (pinyin, English, formula)
        if _is_ascii_line(line):
            if buf:
                merged.append(buf)
                buf = ''
            merged.append(line)
            continue

        # Content line: decide whether to merge
        if not buf:
            buf = line
        else:
            # Merge if previous line doesn't end with sentence-ending punctuation
            if buf[-1] not in _SENTENCE_END and buf[-1] not in _CLAUSE_END:
                buf += line
            elif buf[-1] in _CLAUSE_END:
                buf += line
            else:
                # Sentence ended → start new paragraph
                merged.append(buf)
                buf = line

    if buf:
        merged.append(buf)

    # Phase 3: Normalize whitespace
    result = []
    for line in merged:
        # Collapse multiple spaces
        line = re.sub(r' +', ' ', line)
        result.append(line)

    return '\n'.join(result)

def get_file_map():
    """Build fid → filename mapping (must match server.py)"""
    m = {}
    for f in os.listdir(BASE):
        if not f.endswith('.pdf'): continue
        if '药典1部' in f: m['pharm1'] = f
        elif '药典2部' in f: m['pharm2'] = f
        elif '化学药' in f and '中药' not in f: m['chem'] = f
        elif '处方集' in f: m['rx'] = f
    return m

def extract_to_cache(entries, file_map, cache, pages_per_entry=3, label=''):
    """Extract text and add to cache dict. Key format: fid|page"""
    import fitz

    # Group by fid
    by_fid = {}
    for entry in entries:
        fid = entry.get('fid', '')
        page = entry.get('page', 0)
        if not fid or page < 1: continue
        if fid not in by_fid: by_fid[fid] = set()
        by_fid[fid].add(page)

    for fid, page_set in by_fid.items():
        if fid not in file_map:
            print(f"  ⚠ 未找到 {fid}")
            continue

        fname = file_map[fid]
        fpath = os.path.join(BASE, fname)
        fsize_mb = os.path.getsize(fpath) / (1024*1024)
        pages = sorted(page_set)
        print(f"  打开 {fname[:60]} ({fsize_mb:.0f}MB) - {len(pages)} 页")

        t0 = time.time()
        doc = fitz.open(fpath)
        total = doc.page_count
        extracted = 0

        for page in pages:
            if page < 1 or page > total: continue
            cache_key = f'{fid}|{page}'
            if cache_key in cache: continue  # dedup

            texts = []
            for p in range(page - 1, min(page - 1 + pages_per_entry, total)):
                try:
                    t = doc[p].get_text()
                    t = reformat_text(t)
                    if t.strip():
                        texts.append(t)
                except Exception:
                    pass

            if texts:
                cache[cache_key] = '\n\n'.join(texts)[:5000]
            extracted += 1

            if extracted % 500 == 0:
                elapsed = time.time() - t0
                print(f"    {extracted}/{len(pages)} ({elapsed:.0f}s)...")

        doc.close()
        elapsed = time.time() - t0
        print(f"  完成 {label}: {extracted} 页 ({elapsed:.0f}s)")

def main():
    print("=" * 50)
    print("预提取药典 & 临床用药须知 → page_cache.json.gz")
    print("=" * 50)

    file_map = get_file_map()
    print(f"PDF映射: { {k: v[:40]+'...' for k,v in file_map.items()} }")

    cache = {}  # key: fid|page → text

    # 1. Pharmacopoeia
    pharm_path = os.path.join(BASE, 'pharmacopoeia_index.json')
    with open(pharm_path, 'r', encoding='utf-8') as f:
        pharm = json.load(f)
    print(f"\n📖 药典: {len(pharm)} 条")
    extract_to_cache(pharm, file_map, cache, pages_per_entry=3, label='药典')

    # 2. Clinical references
    clin_path = os.path.join(BASE, 'clinical_ref_index.json')
    with open(clin_path, 'r', encoding='utf-8') as f:
        clin = json.load(f)

    for section in ['chem', 'rx']:
        items = clin.get(section, [])
        if not items: continue
        pages = 4 if section == 'chem' else 2
        print(f"\n📖 临床 [{section}]: {len(items)} 条")
        extract_to_cache(items, file_map, cache, pages_per_entry=pages, label=section)

    # Save cache
    cache_path = os.path.join(BASE, 'page_cache.json')
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)
    with open(cache_path, 'rb') as f_in:
        with gzip.open(cache_path + '.gz', 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    csize = os.path.getsize(cache_path) / 1024
    gsize = os.path.getsize(cache_path + '.gz') / 1024
    print(f"\npage_cache.json: {csize:.0f}KB, .gz: {gsize:.0f}KB")
    print(f"缓存条目: {len(cache)}")
    print("\n✅ 完成")

if __name__ == '__main__':
    main()
