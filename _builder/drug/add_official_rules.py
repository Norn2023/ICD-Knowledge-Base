"""
Add official insurance catalog restrictions (note field) as audit rules
for ALL drugs that have prescribing data.
"""
import json, sys, os, gzip

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    updated = 0
    for d in drugs:
        note = (d.get('note') or '').strip()
        rx = d.get('prescribing')
        if not note or not rx:
            continue

        # Check if note is already in insurance_notes
        notes = rx.get('insurance_notes', [])
        note_texts = [n.get('text', '') for n in notes]
        if any(note in t or t in note for t in note_texts):
            continue  # already included

        # Add official restriction as the highest-priority rule
        official_rule = {
            'risk': 'high',
            'text': '【医保目录限定】' + note,
            'materials': ['病历记录符合目录限定条件', '相关检查/检验报告（证明符合限定条件）']
        }
        # Insert at the beginning (highest priority)
        notes.insert(0, official_rule)
        rx['insurance_notes'] = notes
        updated += 1
        print(f"  {d['name']}: +官方限定: {note[:70]}")

    # Count total notes added
    print(f"\n已更新: {updated} 个药品")
    total_notes = sum(len(d.get('prescribing', {}).get('insurance_notes', [])) for d in drugs if d.get('prescribing'))
    print(f"审核规则总数: {total_notes}")

    drugs_path = os.path.join(BASE, 'drugs.json')
    with open(drugs_path, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(drugs_path, 'rb') as fi:
        with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as fo:
            fo.write(fi.read())

    print("✅ Saved")

if __name__ == '__main__':
    main()
