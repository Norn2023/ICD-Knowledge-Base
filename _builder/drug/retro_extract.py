"""Retroactively extract fields from existing uploaded PDFs and generate .meta.json files."""
import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

_RE_DRUG_FIELDS = [
    ('reg_name',    r'通用名称[：:]\s*([^\n]+)'),
    ('trade_name',  r'商品名称[：:]\s*([^\n]+)'),
    ('en_name',     r'英文名称[：:]\s*([^\n]+)'),
    ('spec',        r'【规格】\s*\n?\s*([^\n【]+)'),
    ('packaging',   r'【包装】\s*\n?\s*([^【]+?)(?:\n【|$)'),
    ('approval',    r'(?:【批准文号】|批准文号)[：:\s]*((?:国药)?[准字包字][\w]+)'),
    ('manufacturer', r'(?:【生产企业】|【药品上市许可持有人】)[\s\S]*?名称[：:]\s*([^\n]+)'),
    ('dosage_form', r'注册剂型[：:]\s*([^\n]+)'),
]

def _extract_drug_fields(filepath):
    result = {}
    ext = os.path.splitext(filepath)[1].lower()
    if ext != '.pdf':
        return result
    try:
        import fitz
        doc = fitz.open(filepath)
        all_text = []
        for i in range(doc.page_count):
            all_text.append(doc[i].get_text('text'))
        doc.close()
        full_text = '\n'.join(all_text)
        # Encoding recovery
        if '【药品名称】' not in full_text and '通用名称' not in full_text:
            recovered = []
            for t in all_text:
                try:
                    recovered.append(t.encode('latin-1').decode('utf-8', errors='replace'))
                except:
                    recovered.append(t)
            full_text = '\n'.join(recovered)
        if '通用名称' not in full_text and '【药品名称】' not in full_text:
            return result
        for field_name, pattern in _RE_DRUG_FIELDS:
            m = re.search(pattern, full_text)
            if m:
                val = re.sub(r'\s+', ' ', m.group(1).strip()).strip()
                if val and len(val) > 1:
                    result[field_name] = val
        # Infer dosage_form from drug name
        if 'dosage_form' not in result and 'reg_name' in result:
            for fm in ['注射用','注射液','片','胶囊','颗粒','口服液','糖浆','丸','软膏','乳膏','凝胶','滴眼液','滴耳液','喷雾剂','气雾剂','栓','贴膏','贴剂','洗剂','搽剂','散','吸入剂']:
                if fm in result['reg_name']:
                    result['dosage_form'] = fm
                    break
        # Broad manufacturer
        if 'manufacturer' not in result:
            m = re.search(r'企业名称[：:]\s*([^\n]+)', full_text)
            if m: result['manufacturer'] = m.group(1).strip()
        # Broad approval
        if 'approval' not in result:
            m = re.search(r'(?:批准文号|国药准字)[：:\s]*([\w]+)', full_text)
            if m:
                val = m.group(1).strip()
                if len(val) >= 8:
                    result['approval'] = '国药准字' + val if not val.startswith('国药') else val
        return result
    except Exception as e:
        print(f'  Error: {e}')
        return {}

def main():
    uploads_dir = os.path.join(BASE, 'uploads')
    if not os.path.isdir(uploads_dir):
        print("No uploads directory")
        return

    processed = 0
    for root, dirs, files in os.walk(uploads_dir):
        for f in files:
            if f.endswith('.meta.json'):
                continue
            fpath = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext != '.pdf':
                continue

            # Skip if meta already exists
            meta_name = os.path.splitext(f)[0] + '.meta.json'
            meta_path = os.path.join(root, meta_name)
            if os.path.exists(meta_path):
                continue

            print(f'Extracting: {f[:50]}...')
            fields = _extract_drug_fields(fpath)
            if fields:
                with open(meta_path, 'w', encoding='utf-8') as mf:
                    json.dump(fields, mf, ensure_ascii=False)
                print(f'  → {len(fields)} fields: {list(fields.keys())}')
                processed += 1
            else:
                print(f'  → No fields extracted (scanned PDF or non-standard format)')

    print(f'\nRetroactively processed: {processed} files')

if __name__ == '__main__':
    main()
