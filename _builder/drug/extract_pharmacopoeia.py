"""
Extract drug monograph index from Chinese Pharmacopoeia (2025) PDFs
Strategy: find Chinese drug names followed by pinyin/English names
"""
import fitz, json, sys, os, re

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))

# Pharmacopoeia volumes
VOLUMES = [
    {'file': '2025版药典1部(OCR).pdf', 'name': '一部·中药', 'type': '中药'},
    {'file': '2025版药典2部(OCR).pdf', 'name': '二部·化学药', 'type': '化学药'},
]

OUTPUT = os.path.join(BASE, 'pharmacopoeia_index.json')

def is_drug_name(text):
    """Strict check: Chinese drug monograph title (2-15 pure CJK chars)"""
    if not text: return False
    text = text.strip()
    # Must be pure CJK (no spaces, punctuation, digits, ASCII)
    if not all('一' <= c <= '鿿' for c in text):
        return False
    # Drug names are typically 2-15 characters
    if len(text) < 2 or len(text) > 18:
        return False
    # Exclude common non-drug text
    exclude = {
        '中国药典', '中华人民共和国药典', '凡例', '通则', '目录', '索引', '前言',
        '附录', '正文', '品种正文', '品名', '汉语拼音', '英文名', '拉丁名',
        '本品', '本品为', '供试品', '对照品', '标准品', '饮片', '颗粒剂',
        '干燥', '粉碎', '取本品', '精密称', '测定法', '色谱条件',
        '系统适用性', '理论板数', '不得过', '应不低于', '加水',
        '加乙醇', '加甲醇', '加乙腈', '加流动相', '滤过', '取续滤液',
        '作为供试品', '另取', '同法', '依法', '限度', '计算公式',
        '含量测定', '鉴别', '检查', '性状', '贮藏', '制剂',
        '类别', '规格', '批准文号', '执行标准', '说明书',
        '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
        '十一', '十二', '十三', '十四', '十五', '十六',
        '溶液', '试验', '方法', '操作', '时间', '温度', '浓度',
        '色谱', '结果', '计算', '测定', '滴定', '称定',
        '空白', '标准', '样品', '试剂', '试药', '缓冲',
        '重量', '体积', '密度', '比例', '日期', '批号',
        '修订', '新增', '删除', '年版', '附则', '说明',
        '原药材', '药材', '粉末', '提取物', '浸膏', '流浸膏',
        '片剂', '胶囊', '注射液', '颗粒', '口服液', '滴丸',
    }
    if text in exclude: return False
    # Exclude text containing measurement units
    if any(unit in text for unit in ['mg', 'ml', 'g', 'μg', 'mm', 'cm', 'mol', 'μm', 'nm']):
        return False
    return True

def is_pinyin_or_english(text):
    """Strict check: pinyin or English drug name (letters and spaces only)"""
    if not text: return False
    text = text.strip()
    # Must be purely ASCII letters and optional spaces
    if not re.match(r'^[A-Z][A-Za-z\s\-]+$', text):
        return False
    # Reasonable length
    if len(text) < 3 or len(text) > 60:
        return False
    # Must have at least some lowercase letters (typical for pinyin)
    if not any(c.islower() for c in text):
        return False
    # Exclude single uppercase + numbers (chemical formulas)
    # Exclude common technical terms
    exclude_words = {'GMP', 'ICH', 'HPLC', 'GC', 'UV', 'IR', 'NMR', 'MS',
                     'PEG', 'SDS', 'TLC', 'RSD', 'SD', 'CV', 'LD', 'ED',
                     'API', 'BP', 'EP', 'JP', 'USP', 'CP', 'ChP'}
    words = text.split()
    if any(w in exclude_words for w in words):
        return False
    return True

def extract_volume(vol_info):
    """Extract drug names and pages from one volume"""
    path = os.path.join(BASE, vol_info['file'])
    if not os.path.exists(path):
        print(f"  ⚠ 文件不存在: {path}")
        return []

    print(f"  打开: {vol_info['file']}...")
    doc = fitz.open(path)
    total = doc.page_count
    entries = []

    for page_num in range(total):
        if page_num % 200 == 0:
            print(f"    处理页码 {page_num+1}/{total}... ({len(entries)} 词条)")

        try:
            text = doc[page_num].get_text()
        except:
            continue

        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if len(lines) < 3:
            continue

        # Strategy: Find drug name candidates and pinyin candidates on this page
        drug_candidates = []  # (line_index, text)
        pinyin_candidates = []  # (line_index, text)

        for i, line in enumerate(lines):
            # Drug name: pure CJK, 2-15 chars, appears early in page (top header)
            if is_drug_name(line):
                drug_candidates.append((i, line))
            # Pinyin: starts with uppercase, all letters/spaces
            elif is_pinyin_or_english(line):
                pinyin_candidates.append((i, line))

        if not drug_candidates:
            continue

        # For each drug candidate, find the nearest pinyin that comes after it
        # Drug monograph names often appear as page headers (line 0-3)
        for di, dname in drug_candidates:
            # Skip drug names that appear to be part of running text
            # (drug names as page headers are at the very top)
            if di > 10:  # drug name deeper in the page is likely just mentioned, not a monograph title
                continue

            # Find closest pinyin after this drug name
            best_pinyin = ''
            best_latin = ''
            best_dist = 999

            for pi, pname in pinyin_candidates:
                if pi > di:
                    dist = pi - di
                    if dist < best_dist:
                        best_dist = dist
                        best_pinyin = pname
                        # Check if next line after pinyin is a Latin name
                        if pi + 1 < len(lines) and re.match(r'^[A-Z][A-Z\s]+$', lines[pi+1]):
                            best_latin = lines[pi+1]

            if best_pinyin and best_dist <= 15:  # pinyin within reasonable distance
                entry = {
                    'name': dname,
                    'pinyin': best_pinyin,
                    'volume': vol_info['name'],
                    'type': vol_info['type'],
                    'page': page_num + 1,
                }
                if best_latin:
                    entry['latin'] = best_latin
                entries.append(entry)

    doc.close()

    # Deduplicate: keep only first occurrence of each drug name (by page order)
    seen = {}
    unique_entries = []
    for e in entries:
        if e['name'] not in seen:
            seen[e['name']] = e
            unique_entries.append(e)

    print(f"    完成: {len(unique_entries)} 词条 (原始 {len(entries)})")
    return unique_entries

def main():
    print("=" * 60)
    print("中国药典2025版 - 药品词条索引提取")
    print("=" * 60)

    all_entries = []
    for vol in VOLUMES:
        print(f"\n[{vol['name']}]")
        entries = extract_volume(vol)
        all_entries.extend(entries)

    print(f"\n{'=' * 60}")
    print(f"总计: {len(all_entries)} 个药典词条")

    # Deduplicate by name
    seen = set()
    unique = []
    for e in all_entries:
        key = e['name']
        if key not in seen:
            seen.add(key)
            unique.append(e)

    print(f"去重后: {len(unique)} 词条")

    # Save
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=1)

    import gzip
    gz_path = OUTPUT + '.gz'
    with open(OUTPUT, 'rb') as f_in:
        with gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    print(f"\n✓ 保存: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f} KB)")
    print(f"✓ 压缩: {gz_path} ({os.path.getsize(gz_path)/1024:.0f} KB)")

    # Sample
    print("\n词条样例:")
    for e in unique[:15]:
        latin = f" [{e['latin']}]" if e.get('latin') else ""
        print(f"  {e['name']} ({e['pinyin']}) → {e['volume']} 第{e['page']}页{latin}")

if __name__ == '__main__':
    main()
