"""
Tag drugs with 上海大病 labels — v2 with strict matching.
"""
import json, gzip

BASE = 'D:/AI_libra/codex_Obsi/_builder/drug'

with open(f'{BASE}/drugs.json', 'r', encoding='utf-8') as f:
    drugs = json.load(f)

# Clear existing tags
for d in drugs:
    if 'tags' in d:
        d['tags'] = []

def has_any(text, keywords):
    """Check if any keyword is in text."""
    for kw in keywords:
        if kw in text:
            return True
    return False

# ============================================================
# STRICT MATCHING RULES
# Each drug is checked against these rules in order.
# Format: (大病标签, category条件, subcat条件, 必须含有的关键词, 排除关键词)
# ============================================================

RULES = [
    # ========== 1. 恶性肿瘤-化学治疗 ==========
    # 经典化疗药：烷化剂、抗代谢、植物碱、细胞毒抗生素、铂类等
    {
        'label': '大病-恶性肿瘤(化疗)',
        'cat_ok': ['抗肿瘤药及免疫调节剂'],
        'subcat_ok': ['抗肿瘤药'],
        'must_name': ['氮芥', '环磷酰胺', '异环磷酰胺', '美法仑', '苯丁酸氮芥', '白消安', '卡莫司汀', '洛莫司汀',
                    '司莫司汀', '替莫唑胺', '达卡巴嗪', '顺铂', '卡铂', '奥沙利铂', '奈达铂', '洛铂',
                    '甲氨蝶呤', '氟尿嘧啶', '替加氟', '卡培他滨', '阿糖胞苷', '吉西他滨', '氟达拉滨',
                    '克拉屈滨', '培美曲塞', '雷替曲塞', '羟基脲', '长春碱', '长春新碱', '长春地辛',
                    '长春瑞滨', '紫杉醇', '多西他赛', '伊立替康', '拓扑替康', '依托泊苷', '替尼泊苷',
                    '多柔比星', '表柔比星', '吡柔比星', '柔红霉素', '伊达比星', '博来霉素', '平阳霉素',
                    '丝裂霉素', '放线菌素', '米托蒽醌', '三氧化二砷', '门冬酰胺酶', '培门冬酶'],
    },
    # 化疗辅助药（止吐、升白等）— 仅限肿瘤科专用
    {
        'label': '大病-恶性肿瘤(化疗辅助)',
        'cat_ok': ['抗肿瘤药及免疫调节剂', '消化道和代谢方面的药物'],
        'must_name': ['昂丹司琼', '格拉司琼', '托烷司琼', '帕洛诺司琼', '阿瑞匹坦', '福沙匹坦',
                    '重组人粒细胞', '聚乙二醇化重组人粒细胞', '重组人白介素', '重组人血小板生成素',
                    '氨磷汀', '美司钠', '右雷佐生', '亚叶酸钙', '左亚叶酸钙'],
        'must_sub': ['止吐药和止恶心药', '免疫兴奋剂', '抗肿瘤药', '所有其他治疗用药物'],
    },

    # ========== 2. 恶性肿瘤-内分泌治疗 ==========
    {
        'label': '大病-恶性肿瘤(内分泌)',
        'cat_ok': ['抗肿瘤药及免疫调节剂'],
        'subcat_ok': ['内分泌治疗用药'],
        'must_name': ['他莫昔芬', '来曲唑', '阿那曲唑', '依西美坦', '氟维司群', '戈舍瑞林',
                    '亮丙瑞林', '曲普瑞林', '比卡鲁胺', '氟他胺', '恩杂鲁胺', '阿比特龙',
                    '地加瑞克', '阿帕他胺', '达罗他胺', '瑞维鲁胺', '阿帕鲁胺', '达洛鲁胺'],
    },

    # ========== 3. 恶性肿瘤-靶向治疗 ==========
    {
        'label': '大病-恶性肿瘤(靶向)',
        'cat_ok': ['抗肿瘤药及免疫调节剂'],
        'must_name': ['伊马替尼', '吉非替尼', '厄洛替尼', '埃克替尼', '阿法替尼', '达克替尼',
                    '奥希替尼', '阿美替尼', '伏美替尼', '克唑替尼', '色瑞替尼', '阿来替尼',
                    '劳拉替尼', '恩沙替尼', '达拉非尼', '曲美替尼', '考比替尼', '维莫非尼',
                    '伊布替尼', '泽布替尼', '奥布替尼', '阿卡替尼', '芦可替尼', '菲卓替尼',
                    '舒尼替尼', '索拉非尼', '仑伐替尼', '安罗替尼', '阿帕替尼', '瑞戈非尼',
                    '呋喹替尼', '培唑帕尼', '阿昔替尼', '卡博替尼', '凡德他尼', '拉帕替尼',
                    '吡咯替尼', '来那替尼', '奈拉替尼', '哌柏西利', '阿贝西利', '达尔西利',
                    '奥拉帕利', '尼拉帕利', '氟唑帕利', '帕米帕利', '芦卡帕利',
                    '维奈克拉', '艾伏尼布', '塞利尼索', '西达本胺', '硼替佐米',
                    '利妥昔单抗', '曲妥珠单抗', '帕妥珠单抗', '贝伐珠单抗', '西妥昔单抗',
                    '尼妥珠单抗', '雷莫西尤单抗', '维迪西妥单抗', '恩美曲妥珠单抗',
                    '德曲妥珠单抗', '戈沙妥珠单抗', '维布妥昔单抗', '奥加伊妥珠单抗',
                    '地舒单抗', '达雷妥尤单抗', '埃罗妥珠单抗', '伊沙佐米', '来那度胺',
                    '泊马度胺', '沙利度胺', '卡非佐米', '达沙替尼', '尼洛替尼', '博舒替尼',
                    '普纳替尼', '氟马替尼', '奥雷巴替尼'],
    },

    # ========== 4. 恶性肿瘤-免疫治疗 ==========
    {
        'label': '大病-恶性肿瘤(免疫)',
        'cat_ok': ['抗肿瘤药及免疫调节剂'],
        'must_name': ['帕博利珠单抗', '纳武利尤单抗', '卡瑞利珠单抗', '信迪利单抗',
                    '替雷利珠单抗', '特瑞普利单抗', '阿替利珠单抗', '度伐利尤单抗',
                    '派安普利单抗', '斯鲁利单抗', '普特利单抗', '恩沃利单抗',
                    '伊匹木单抗', '卡度尼利单抗', '重组人血管内皮抑制素'],
    },

    # ========== 5. 恶性肿瘤-中医治疗 ==========
    {
        'label': '大病-恶性肿瘤(中医)',
        'type_ok': ['中成药'],
        'subcat_ok': ['肿瘤用药', '肿瘤辅助用药'],
        'must_name': [],
    },

    # ========== 6. 肾移植抗排异 ==========
    {
        'label': '大病-肾移植抗排异',
        'must_name': ['环孢素', '他克莫司', '西罗莫司', '依维莫司', '吗替麦考酚酯',
                    '麦考酚钠', '硫唑嘌呤', '咪唑立宾', '来氟米特', '巴利昔单抗',
                    '抗人T细胞兔免疫球蛋白', '抗人T细胞猪免疫球蛋白', '兔抗人胸腺细胞免疫球蛋白',
                    '贝拉西普', '抗淋巴细胞球蛋白'],
        # Only if it's for transplant, filter out topical forms
        'exclude_form': [],
    },

    # ========== 7. 重症尿毒症透析-贫血治疗 ==========
    {
        'label': '大病-尿毒症透析',
        'cat_ok': ['血液和造血器官药'],
        'subcat_ok': ['抗贫血药'],
        'must_name': ['促红', '红细胞生成素', '依泊汀', '达依泊汀', '罗沙司他',
                    '蔗糖铁', '右旋糖酐铁', '异麦芽糖酐铁', '羧基麦芽糖铁',
                    '多糖铁', '富马酸亚铁', '琥珀酸亚铁', '硫酸亚铁', '蛋白琥珀酸铁'],
    },
    # 透析钙磷调节
    {
        'label': '大病-尿毒症透析',
        'cat_ok': ['消化道和代谢方面的药物', '系统用激素制剂', '血液和造血器官药'],
        'subcat_ok': ['矿物质补充剂', '钙稳态药', '维生素类', '所有其他治疗用药物'],
        'must_name': ['司维拉姆', '碳酸镧', '西那卡塞', '依特卡肽', '帕立骨化醇',
                    '骨化三醇', '阿法骨化醇', '醋酸钙', '碳酸钙'],
        'must_note': ['高磷', '透析', 'CKD', '慢性肾脏病', '继发性甲旁亢', '肾性'],
    },

    # ========== 8. 精神病-精神分裂症/偏执 ==========
    {
        'label': '大病-精神病(精分/偏执)',
        'cat_ok': ['神经系统药物'],
        'subcat_ok': ['精神安定药'],
        'must_name': ['氯丙嗪', '奋乃静', '氟奋乃静', '三氟拉嗪', '硫利达嗪',
                    '氟哌啶醇', '氟哌利多', '五氟利多', '氯氮平', '奥氮平',
                    '喹硫平', '利培酮', '帕利哌酮', '阿立哌唑', '氨磺必利',
                    '齐拉西酮', '布南色林', '哌罗匹隆', '舒必利', '氯普噻吨',
                    '氟哌噻吨', '珠氯噻醇', '洛沙平'],
    },

    # ========== 9. 精神病-抑郁症/强迫症 ==========
    {
        'label': '大病-精神病(抑郁/强迫)',
        'cat_ok': ['神经系统药物'],
        'subcat_ok': ['精神安定药', '精神兴奋药'],
        'must_name': ['氟西汀', '帕罗西汀', '舍曲林', '氟伏沙明', '西酞普兰',
                    '艾司西酞普兰', '文拉法辛', '度洛西汀', '米氮平', '曲唑酮',
                    '阿戈美拉汀', '伏硫西汀', '安非他酮', '米那普仑', '瑞波西汀',
                    '阿米替林', '氯米帕明', '马普替林', '多塞平', '米安色林',
                    '吗氯贝胺', '苯乙肼', '圣约翰草'],
    },

    # ========== 10. 精神病-躁狂症/癫痫伴精神障碍 ==========
    {
        'label': '大病-精神病(躁狂/癫痫)',
        'cat_ok': ['神经系统药物'],
        'subcat_ok': ['抗癫痫药', '精神安定药'],
        'must_name': ['碳酸锂', '丙戊酸钠', '丙戊酸镁', '丙戊酰胺', '拉莫三嗪',
                    '卡马西平', '奥卡西平', '艾司利卡西平',
                    # Only these antiepileptics used for bipolar/psychiatric
                    '托吡酯'],
    },
]

# Apply rules
tagged_count = 0
for drug in drugs:
    drug['tags'] = []
    dtype = drug.get('type', '')
    cat = drug.get('cat', '')
    subcat = drug.get('subcat', '')
    subsubcat = drug.get('subsubcat', '')
    name = drug.get('name', '')
    note = drug.get('note', '')
    form = drug.get('form', '')

    # Collect insurance notes text
    prescribing = drug.get('prescribing', {})
    ins_notes = prescribing.get('insurance_notes', [])
    ins_text = ' '.join(n.get('text', '') for n in ins_notes)

    for rule in RULES:
        label = rule['label']
        if drug['tags']:
            continue

        # Type check (for 中成药 vs 西药)
        if 'type_ok' in rule:
            if dtype not in rule['type_ok']:
                continue

        # Category check
        if 'cat_ok' in rule:
            if not any(c in cat for c in rule['cat_ok']):
                continue

        # Subcategory check
        if 'subcat_ok' in rule:
            matched_sub = False
            for s in rule['subcat_ok']:
                if s in subcat or s in subsubcat:
                    matched_sub = True
                    break
            if not matched_sub:
                continue

        # Must-name check
        if 'must_name' in rule and rule['must_name']:
            if not has_any(name, rule['must_name']):
                continue

        # Must-note check (optional)
        if 'must_note' in rule and rule['must_note']:
            combined = note + ' ' + ins_text
            if not has_any(combined, rule['must_note']):
                continue

        # Exclude form check
        if 'exclude_form' in rule and rule['exclude_form']:
            if has_any(form, rule['exclude_form']):
                continue

        drug['tags'].append(label)
        tagged_count += 1

print(f'Tagged {tagged_count} drugs (strict matching)')

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
import gzip as gz
json_bytes = json.dumps(drugs, ensure_ascii=False).encode('utf-8')
with gz.open(f'{BASE}/drugs.json.gz', 'wb', compresslevel=6) as f:
    f.write(json_bytes)
print(f'\nSaved ({len(json_bytes)} bytes)')

# Summary
summary = []
for drug in drugs:
    if drug.get('tags'):
        summary.append({
            'name': drug['name'],
            'cat': drug.get('cat', ''),
            'subcat': drug.get('subcat', ''),
            'tags': drug['tags'],
            'note': drug.get('note', '')[:80],
        })

with open(f'{BASE}/_dabing_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f'Summary: {len(summary)} drugs')
