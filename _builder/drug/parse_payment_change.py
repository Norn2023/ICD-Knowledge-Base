"""
Parse 2025 payment scope change PDF (65 drugs), cross-reference with drugs.json.
"""
import fitz, json, sys, os, gzip, re

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    if not s: return ''
    return re.sub(r'[\s（）()　ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ\-]+', '', str(s))

def main():
    print("=" * 60)
    print("解析 2025医保支付范围变化 → 同步药品")
    print("=" * 60)

    # Parse PDF - line by line
    pdf_path = os.path.join(BASE, '2025年医保药品目录医保支付范围变化的药品名单（共65种）.pdf')
    doc = fitz.open(pdf_path)

    all_lines = []
    for p in range(doc.page_count):
        t = doc[p].get_text()
        all_lines.extend(l.strip() for l in t.split('\n') if l.strip())

    # Skip header (lines 0-6)
    all_lines = all_lines[7:]
    doc.close()

    # Parse entries: each starts with a digit-only line
    entries = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        if re.match(r'^\d+$', line):
            seq = int(line)
            cat = all_lines[i+1] if i+1 < len(all_lines) else ''
            dtype = all_lines[i+2] if i+2 < len(all_lines) else ''
            drug_name = all_lines[i+3] if i+3 < len(all_lines) else ''
            i += 4

            # Next lines: dosage form (may be 1-2 lines), then v2024, then v2025
            # Dosage form ends when we hit a restriction line or "—"
            form_parts = []
            while i < len(all_lines):
                nl = all_lines[i]
                if nl.startswith('限') or nl == '—':
                    break
                if re.match(r'^\d+$', nl):  # next entry
                    break
                form_parts.append(nl)
                i += 1

            dosage_form = ' '.join(form_parts)

            # v2024 restriction
            v2024_parts = []
            while i < len(all_lines):
                nl = all_lines[i]
                if re.match(r'^\d+$', nl):  # next entry
                    break
                # Check if this is the start of v2025
                # v2025 starts with "限" after v2024 has accumulated something or "—"
                if v2024_parts and (nl.startswith('限') or nl == '—'):
                    # This is v2025
                    break
                v2024_parts.append(nl)
                i += 1

            v2024 = ' '.join(v2024_parts).strip()
            if v2024 == '—': v2024_clean = ''
            else: v2024_clean = re.sub(r'^限[：:]?\s*', '', v2024)

            # v2025 restriction
            v2025_parts = []
            while i < len(all_lines):
                nl = all_lines[i]
                if re.match(r'^\d+$', nl):  # next entry
                    break
                v2025_parts.append(nl)
                i += 1

            v2025 = ' '.join(v2025_parts).strip()
            if v2025 == '—': v2025_clean = ''
            else: v2025_clean = re.sub(r'^限[：:]?\s*', '', v2025)

            # Determine change type
            if not v2024_clean and v2025_clean:
                change_type = '新增限定'
                change_detail = v2025_clean[:120]
            elif v2024_clean and not v2025_clean:
                change_type = '解除限定'
                change_detail = '原限定已取消'
            elif v2024_clean != v2025_clean:
                change_type = '限定修改'
                change_detail = '内容变更'
            else:
                change_type = '不变'
                change_detail = ''

            entries.append({
                'seq': seq, 'cat': cat, 'type': dtype,
                'name': drug_name, 'form': dosage_form,
                'v2024': v2024_clean[:300], 'v2025': v2025_clean[:300],
                'change_type': change_type, 'change_detail': change_detail
            })
        else:
            i += 1

    print(f"PDF解析: {len(entries)} 条记录")

    # Load drugs and match
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    matched = 0
    unmatched_entries = []

    for entry in entries:
        name = entry['name']
        nn = norm(name)

        best_match = None
        best_score = 0

        for d in drugs:
            dn = norm(d.get('name', ''))
            if not dn or not nn:
                continue
            # Score: exact > contains > substring
            score = 0
            if dn == nn:
                score = 100
            elif len(nn) >= 4 and len(dn) >= 4:
                if nn in dn:
                    score = 80 + len(nn)/len(dn)*10
                elif dn in nn:
                    score = 70 + len(dn)/len(nn)*10

            if score > best_score:
                best_score = score
                best_match = d

        if best_match and best_score >= 70:
            d = best_match
            d['_payment_change'] = {
                'type': entry['change_type'],
                'detail': entry['change_detail'],
                'v2024': entry['v2024'],
                'v2025': entry['v2025'],
                'summary': f"【{entry['change_type']}】{entry['v2024'][:60] if entry['v2024'] else '（无限定）'} → {entry['v2025'][:60] if entry['v2025'] else '（无限定）'}"
            }
            matched += 1
            print(f"  ✓ {name} → {d['name']} ({entry['change_type']})")
        else:
            unmatched_entries.append(entry)

    print(f"\n匹配成功: {matched}/{len(entries)}")
    print(f"未匹配: {len(unmatched_entries)}")
    for u in unmatched_entries[:15]:
        print(f"  ✗ #{u['seq']} {u['name']} ({u['change_type']})")

    # Also update the official note for matched drugs that have 2025 restriction
    for entry in entries:
        nn = norm(entry['name'])
        for d in drugs:
            dn = norm(d.get('name', ''))
            if dn == nn or (len(nn)>=4 and len(dn)>=4 and (nn in dn or dn in nn)):
                if entry['v2025'] and not d.get('note'):
                    d['note'] = '限' + entry['v2025']
                break

    # Save
    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print(f"\n✅ Saved — {matched} drugs tagged")

    # Summary by change type
    from collections import Counter
    types = Counter(e['change_type'] for e in entries)
    print(f"变化类型分布: {dict(types)}")

if __name__ == '__main__':
    main()
