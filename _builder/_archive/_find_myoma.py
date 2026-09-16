import json
d=json.load(open('web/data.json','r',encoding='utf-8'))
print("=== Diagnosis (子宫肌瘤) ===")
dx=[c for c in d['icd10'] if '子宫' in c['n'] and ('平滑肌' in c['n'] or '肌瘤' in c['n'])]
for c in dx[:15]:
    print(f"  {c['c']} {c['n']}")

print("\n=== Procedure (子宫肌瘤切除) ===")
px=[c for c in d['icd9'] if '子宫' in c['n'] and '肌瘤' in c['n']]
for c in px[:10]:
    print(f"  {c['c']} {c['n']}")

# Check DRG mapping
print("\n=== DRG dx lookup ===")
drg=json.load(open('web/drg.json','r',encoding='utf-8'))
for c in dx[:5]:
    maps=drg.get('dx2a',{}).get(c['c'],[])
    if maps: print(f"  {c['c']} -> {[(m['a'],m['an'][:40]) for m in maps]}")
    else: print(f"  {c['c']} -> NO MATCH")

print("\n=== DRG px lookup ===")
for c in px[:8]:
    maps=drg.get('px2a',{}).get(c['c'],[])
    if maps: print(f"  {c['c']} -> {[(m['a'],m['an'][:40]) for m in maps]}")
    else: print(f"  {c['c']} -> NO MATCH")
