"""
Tag drugs with 上海大病 (catastrophic disease) labels based on indications and categories.

上海大病范畴:
1. 重症尿毒症透析治疗
2. 肾移植抗排异治疗
3. 恶性肿瘤治疗（化学治疗、内分泌特异治疗、放射治疗、同位素治疗、介入治疗、中医治疗）
4. 部分精神病病种治疗（精神分裂症、中重度抑郁症、躁狂症、强迫症、精神发育迟缓伴发精神障碍、癫痫伴发精神障碍、偏执性精神病）
"""
import json
import gzip
import re

BASE = 'D:/AI_libra/codex_Obsi/_builder/drug'

with open(f'{BASE}/drugs.json', 'r', encoding='utf-8') as f:
    drugs = json.load(f)

# Define matching rules: (keywords_in_category_or_name, 大病类别)
RULES = [
    # === 恶性肿瘤治疗 ===
    # 化学治疗
    {
        'label': '大病-恶性肿瘤(化疗)',
        'cats': ['抗肿瘤药'],
        'subcats': ['抗肿瘤药', '抗代谢药', '植物生物碱和其他天然药', '细胞毒素类抗生素和有关药物'],
        'name_kw': ['化疗', '抗肿瘤', '抗癌'],
        'note_kw': ['肿瘤', '癌', '白血病', '淋巴瘤', '骨髓瘤', '肉瘤'],
    },
    # 内分泌特异治疗
    {
        'label': '大病-恶性肿瘤(内分泌)',
        'cats': ['抗肿瘤药及免疫调节剂'],
        'subcats': ['内分泌治疗药', '激素拮抗剂和相关药物'],
        'name_kw': ['他莫昔芬', '来曲唑', '阿那曲唑', '依西美坦', '氟维司群', '戈舍瑞林', '亮丙瑞林', '曲普瑞林', '比卡鲁胺', '氟他胺', '恩杂鲁胺', '阿比特龙'],
        'note_kw': ['乳腺癌', '前列腺癌', '内分泌治疗'],
    },
    # 靶向治疗(归入化疗大类)
    {
        'label': '大病-恶性肿瘤(靶向)',
        'cats': ['抗肿瘤药及免疫调节剂'],
        'subcats': ['其他抗肿瘤药', '靶向治疗药'],
        'name_kw': ['替尼', '单抗', '珠单抗', '西妥昔', '贝伐', '利妥昔', '曲妥珠', '帕妥珠', '伊马替尼', '吉非替尼', '厄洛替尼', '克唑替尼', '奥希替尼', '阿来替尼', '奥拉帕利', '尼拉帕利'],
        'note_kw': ['靶向', 'EGFR', 'ALK', 'HER2', 'PD-1', 'PD-L1'],
    },
    # 免疫治疗
    {
        'label': '大病-恶性肿瘤(免疫)',
        'cats': ['抗肿瘤药及免疫调节剂'],
        'subcats': ['免疫兴奋剂', '免疫检查点抑制剂'],
        'name_kw': ['帕博利珠', '纳武利尤', '卡瑞利珠', '信迪利', '替雷利珠', '特瑞普利', '阿替利珠', '度伐利尤'],
        'note_kw': ['免疫治疗', 'PD-1', 'PD-L1', 'CTLA-4'],
    },
    # 中医肿瘤
    {
        'label': '大病-恶性肿瘤(中医)',
        'cats': ['中成药'],
        'subcats': ['肿瘤用药'],
        'name_kw': ['消癌', '抗癌', '华蟾素', '鸦胆子', '复方斑蝥', '康莱特', '艾迪', '参一'],
        'note_kw': ['肿瘤', '癌'],
    },

    # === 肾移植抗排异治疗 ===
    {
        'label': '大病-肾移植抗排异',
        'cats': ['抗肿瘤药及免疫调节剂'],
        'subcats': ['免疫抑制剂'],
        'name_kw': ['环孢素', '他克莫司', '西罗莫司', '依维莫司', '吗替麦考酚酯', '麦考酚钠', '硫唑嘌呤', '咪唑立宾', '来氟米特', '巴利昔单抗', '抗胸腺细胞球蛋白', '抗淋巴细胞球蛋白', '贝拉西普'],
        'note_kw': ['移植', '排异', '排斥'],
    },

    # === 重症尿毒症透析治疗 ===
    {
        'label': '大病-尿毒症透析',
        'cats': ['血液和造血器官药'],
        'subcats': ['抗贫血药'],
        'name_kw': ['促红', '红细胞生成素', '依泊汀', '达依泊汀', '罗沙司他', '蔗糖铁', '右旋糖酐铁', '异麦芽糖酐铁', '羧基麦芽糖铁'],
        'note_kw': ['肾性贫血', '透析', '尿毒症', '慢性肾脏病', 'CKD'],
    },
    # 透析相关用药
    {
        'label': '大病-尿毒症透析',
        'cats': ['消化道和代谢方面的药物', '系统用激素制剂'],
        'subcats': ['矿物质补充剂', '钙稳态药'],
        'name_kw': ['碳酸钙', '醋酸钙', '司维拉姆', '碳酸镧', '骨化三醇', '帕立骨化醇', '西那卡塞', '依特卡肽'],
        'note_kw': ['高磷血症', '继发性甲旁亢', '透析', '慢性肾脏病', 'CKD'],
    },

    # === 精神病治疗 ===
    # 精神分裂症 / 偏执性精神病
    {
        'label': '大病-精神病(精分/偏执)',
        'cats': ['神经系统药物'],
        'subcats': ['精神安定药', '抗精神病药'],
        'name_kw': ['氯丙嗪', '奋乃静', '氟哌啶醇', '氯氮平', '奥氮平', '喹硫平', '利培酮', '帕利哌酮', '阿立哌唑', '氨磺必利', '齐拉西酮', '布南色林', '哌罗匹隆', '五氟利多', '舒必利', '氟哌噻吨', '氯普噻吨'],
        'note_kw': ['精神分裂症', '分裂情感', '偏执', '精神病性'],
    },
    # 中重度抑郁症 / 强迫症
    {
        'label': '大病-精神病(抑郁/强迫)',
        'cats': ['神经系统药物'],
        'subcats': ['抗抑郁药', '精神兴奋药'],
        'name_kw': ['氟西汀', '帕罗西汀', '舍曲林', '氟伏沙明', '西酞普兰', '艾司西酞普兰', '文拉法辛', '度洛西汀', '米氮平', '曲唑酮', '阿戈美拉汀', '伏硫西汀', '安非他酮', '米那普仑', '瑞波西汀', '阿米替林', '氯米帕明', '马普替林'],
        'note_kw': ['抑郁', '强迫', '广泛性焦虑', '惊恐'],
    },
    # 躁狂症 / 癫痫伴发精神障碍
    {
        'label': '大病-精神病(躁狂/癫痫)',
        'cats': ['神经系统药物'],
        'subcats': ['抗癫痫药', '心境稳定剂'],
        'name_kw': ['碳酸锂', '丙戊酸', '丙戊酸钠', '丙戊酸镁', '拉莫三嗪', '卡马西平', '奥卡西平', '托吡酯', '加巴喷丁', '普瑞巴林', '左乙拉西坦'],
        'note_kw': ['躁狂', '双相', '癫痫', '心境稳定'],
    },
]

# Apply tagging
tagged = 0
for drug in drugs:
    if 'tags' not in drug:
        drug['tags'] = []

    cat = drug.get('cat', '')
    subcat = drug.get('subcat', '')
    name = drug.get('name', '')
    note = drug.get('note', '')
    form = drug.get('form', '')

    # Also check prescribing notes
    prescribing = drug.get('prescribing', {})
    insurance_notes = prescribing.get('insurance_notes', [])
    ins_text = ' '.join(n.get('text', '') for n in insurance_notes) if insurance_notes else ''

    # Combine all text for keyword search
    all_text = f'{cat} {subcat} {name} {note} {ins_text}'

    for rule in RULES:
        label = rule['label']
        if label in drug['tags']:
            continue  # already tagged

        matched = False

        # Check category match
        if rule.get('cats'):
            for c in rule['cats']:
                if c in cat:
                    matched = True
                    break

        # Check subcategory match
        if rule.get('subcats'):
            for s in rule['subcats']:
                if s in subcat:
                    matched = True
                    break

        # Check name keywords
        if rule.get('name_kw'):
            for kw in rule['name_kw']:
                if kw in name:
                    matched = True
                    break

        # Check note/insurance keywords
        if not matched and rule.get('note_kw'):
            for kw in rule['note_kw']:
                if kw in all_text:
                    matched = True
                    break

        if matched:
            drug['tags'].append(label)
            tagged += 1

print(f'Tagged {tagged} drug entries')

# Count by label
from collections import Counter
label_counts = Counter()
for drug in drugs:
    for tag in drug.get('tags', []):
        label_counts[tag] += 1

print('\nTags distribution:')
for label, count in label_counts.most_common():
    print(f'  {label}: {count}')

# Save
with open(f'{BASE}/drugs.json', 'w', encoding='utf-8') as f:
    json.dump(drugs, f, ensure_ascii=False)

# Gzip
json_bytes = json.dumps(drugs, ensure_ascii=False).encode('utf-8')
with gzip.open(f'{BASE}/drugs.json.gz', 'wb', compresslevel=6) as f:
    f.write(json_bytes)
print(f'\nSaved drugs.json ({len(json_bytes)} bytes)')
print(f'Gzipped: {len(json_bytes)} -> {len(gzip.compress(json_bytes))} bytes')

# Also save a summary for verification
summary = []
for drug in drugs:
    if drug.get('tags'):
        summary.append({
            'name': drug['name'],
            'cat': drug['cat'],
            'subcat': drug['subcat'],
            'tags': drug['tags'],
            'note': drug.get('note', '')[:80],
        })

with open(f'{BASE}/_dabing_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f'Summary: {len(summary)} drugs tagged with 大病')
