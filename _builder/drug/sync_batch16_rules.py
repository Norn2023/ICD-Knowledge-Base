"""
Sync batch 16 "药品限适应症" rules to drugs.json as official notes
and add to DRUG_INFO insurance_notes for drugs with existing entries.
"""
import json, os, re, gzip, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

# Load batch 16 rules
with open(os.path.join(BASE, 'batch16_rules.json'), 'r', encoding='utf-8') as f:
    batch16 = json.load(f)

print(f"Loaded {len(batch16)} batch 16 rules")

# Load drugs.json
drugs_path = os.path.join(BASE, 'drugs.json')
with open(drugs_path, 'r', encoding='utf-8') as f:
    drugs = json.load(f)

# Build name lookup
drug_by_name = {}
for d in drugs:
    drug_by_name[d['name']] = d

# Match and sync
updated_drugs = 0
matched_rules = {}  # rule_name -> actual drug name in drugs.json

for rule_name, rule_text in batch16.items():
    clean = rule_name.strip().replace('\n', ' ').replace('  ', ' ')
    actual_name = None

    # Try exact match
    if clean in drug_by_name:
        actual_name = clean
    else:
        # Try normalized match
        for dname in drug_by_name:
            if clean.replace(' ', '') == dname.replace(' ', ''):
                actual_name = dname
                break
        if not actual_name:
            # Try substring match
            for dname in drug_by_name:
                if len(clean) > 5 and clean.replace(' ', '') in dname.replace(' ', ''):
                    actual_name = dname
                    break

    if actual_name:
        drug = drug_by_name[actual_name]
        # Set the note field
        drug['note'] = rule_text
        # Also track the source
        drug['_batch16_rule'] = True
        drug['_batch16_source'] = '第十六批药品限适应症'
        matched_rules[rule_name] = actual_name
        updated_drugs += 1

print(f"Updated {updated_drugs} drugs with batch 16 rules")

# Now also sync to DRUG_INFO for drugs that already have entries
with open(os.path.join(BASE, 'build_drug_info.py'), 'r', encoding='utf-8') as f:
    bd_content = f.read()

# Find which DRUG_INFO drugs match batch 16
drinfo_matches = 0
for rule_name, actual_name in matched_rules.items():
    # Check if this drug is in DRUG_INFO
    # Look for the drug key in DRUG_INFO dict
    pattern = rf"\n    '{re.escape(actual_name)}':\s*\{{"
    if re.search(pattern, bd_content):
        rule_text = batch16[rule_name]
        # Add the batch 16 rule as a high-risk insurance note
        new_note = f"            {{'risk': 'high', 'text': '【医保目录限定】{rule_text}', 'materials': ['疾病诊断须符合医保限定支付适应症', '诊断编码须与限定适应症匹配']}},\n"

        # Find the insurance_notes section for this drug and prepend the rule
        # Find the drug entry
        entry_match = re.search(rf"\n    '{re.escape(actual_name)}':\s*\{{", bd_content)
        if entry_match:
            # Find the insurance_notes section within this entry
            start = entry_match.start()
            # Find the matching closing }
            depth = 0
            pos = start
            insurance_start = -1
            while pos < len(bd_content):
                if bd_content[pos:pos+17] == "'insurance_notes'":
                    insurance_start = pos
                    break
                pos += 1

            if insurance_start > start and insurance_start < start + 5000:  # within reasonable range
                # Find the opening [ for insurance_notes list
                bracket_pos = bd_content.find('[', insurance_start)
                if bracket_pos > 0:
                    # Insert after the opening [
                    insert_pos = bracket_pos + 1
                    bd_content = bd_content[:insert_pos] + '\n' + new_note + bd_content[insert_pos:]
                    drinfo_matches += 1

if drinfo_matches > 0:
    print(f"Added batch 16 rules to {drinfo_matches} DRUG_INFO insurance_notes")
    with open(os.path.join(BASE, 'build_drug_info.py'), 'w', encoding='utf-8') as f:
        f.write(bd_content)
    # Rebuild drugs.json
    print("Rebuilding drugs.json...")
    exec(open(os.path.join(BASE, 'build_drug_info.py'), encoding='utf-8').read())

# Save updated drugs.json with note fields
with open(drugs_path, 'w', encoding='utf-8') as f:
    json.dump(drugs, f, ensure_ascii=False, indent=1)
with open(drugs_path, 'rb') as f_in:
    with gzip.open(drugs_path + '.gz', 'wb', compresslevel=9) as f_out:
        f_out.write(f_in.read())

print(f"Done! {updated_drugs} drugs updated, {drinfo_matches} DRUG_INFO entries enhanced")
