"""Extract all drug product records from the 10237-page PDF using y-clustering"""
import fitz, json, sys, os, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = 'D:/AI_libra/codex_Obsi/_builder/drug/医保药品分类与代码数据(西药、中成药)截至2026年6月5日.pdf'
OUTPUT_PATH = 'D:/AI_libra/codex_Obsi/_builder/drug/pdf_products.json'

# Column x-boundaries
COL_BOUNDARIES = [
    (0, 107, '药品代码'), (107, 135, '注册名称'), (135, 157, '注册剂型'),
    (157, 181, '注册规格'), (181, 207, '商品名称'), (207, 227, '剂型'),
    (227, 245, '规格'), (245, 290, '包装材质'), (290, 303, '最小包装数量'),
    (303, 313, '最小制剂单位'), (313, 326, '最小包装单位'), (326, 361, '药品企业'),
    (361, 397, '批准文号'), (397, 450, '药品本位码'),
]

Y_CLUSTER_THRESHOLD = 12  # max y-difference for spans to be in same row
ROW_GAP_THRESHOLD = 20     # min y-gap to consider it a new record's first row

def assign_column(x):
    for x_min, x_max, col_name in COL_BOUNDARIES:
        if x_min <= x < x_max:
            return col_name
    return None

def is_drug_code(text):
    return bool(re.match(r'^[A-Z0-9]{15,}$', text))

def parse_page(page):
    blocks = page.get_text('dict')['blocks']

    # Collect all text spans
    all_spans = []
    for b in blocks:
        if b['type'] != 0:
            continue
        for line in b['lines']:
            y = round(line['bbox'][1], 0)
            for span in line['spans']:
                text = span['text'].strip()
                if not text: continue
                x = round(span['bbox'][0], 0)
                col = assign_column(x)
                if col:
                    all_spans.append((y, x, col, text))

    if not all_spans:
        return []

    # Sort by y, then x
    all_spans.sort(key=lambda t: (t[0], t[1]))

    # Cluster spans into rows by y-proximity
    rows = []
    current_row = [all_spans[0]]
    for span in all_spans[1:]:
        y = span[0]
        prev_y = current_row[-1][0]
        if y - prev_y <= Y_CLUSTER_THRESHOLD:
            current_row.append(span)
        else:
            rows.append(current_row)
            current_row = [span]
    rows.append(current_row)

    # Group rows into records
    # A new record starts at a row that:
    # 1. Contains a 药品代码, AND
    # 2. The y-gap from the previous row's first 药品代码 row is > ROW_GAP_THRESHOLD
    records = []
    current_record_rows = []

    for row_idx, row in enumerate(rows):
        row_spans = sorted(row, key=lambda t: t[1])  # sort by x within row
        has_drug_code = any(col == '药品代码' and is_drug_code(text) for y, x, col, text in row_spans)

        if has_drug_code:
            # Check if this is a new record (gap from last drug code row)
            if current_record_rows:
                # Save previous record
                rec = build_record(current_record_rows)
                if rec.get('药品代码'):
                    records.append(rec)
                current_record_rows = []

        current_record_rows.append(row_spans)

    # Don't forget the last record
    if current_record_rows:
        rec = build_record(current_record_rows)
        if rec.get('药品代码') and is_drug_code(rec['药品代码']):
            records.append(rec)

    return records

def build_record(rows):
    """Build a record from its rows of spans"""
    rec = defaultdict(list)

    # Process all spans in the rows, sorted by y then x
    all_spans = []
    for row in rows:
        all_spans.extend(row)
    all_spans.sort(key=lambda t: (t[0], t[1]))

    for y, x, col, text in all_spans:
        rec[col].append(text)

    record = {}
    for col_name in ['药品代码', '注册名称', '注册剂型', '注册规格', '商品名称',
                     '剂型', '规格', '包装材质', '最小包装数量', '最小制剂单位',
                     '最小包装单位', '药品企业', '批准文号', '药品本位码']:
        texts = rec.get(col_name, [])
        record[col_name] = ''.join(texts).strip()

    return record

def main():
    print(f"Opening PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    total_pages = doc.page_count
    print(f"Total pages: {total_pages}")

    all_records = []

    for page_num in range(total_pages):
        if page_num % 200 == 0:
            print(f"Processing page {page_num+1}/{total_pages}... ({len(all_records)} records so far)")
            # Periodic save to avoid memory issues
            if page_num > 0 and page_num % 2000 == 0:
                with open(OUTPUT_PATH + '.part', 'w', encoding='utf-8') as f:
                    json.dump(all_records, f, ensure_ascii=False, indent=1)

        page = doc[page_num]
        try:
            records = parse_page(page)
            all_records.extend(records)
        except Exception as e:
            print(f"  Warning on page {page_num+1}: {e}")

    doc.close()

    print(f"\nTotal records extracted: {len(all_records)}")

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=1)

    print(f"Saved to {OUTPUT_PATH}")

    drugs = set(r.get('注册名称', '') for r in all_records if r.get('注册名称'))
    print(f"Unique drug names: {len(drugs)}")
    print(f"Sample drugs: {sorted(list(drugs))[:20]}")

if __name__ == '__main__':
    main()
