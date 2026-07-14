"""Generate coding rules knowledge base from DRG data and ICD-10 standards"""
import json, gzip, os, re

base = os.path.dirname(os.path.abspath(__file__))

with gzip.open(os.path.join(base, 'drg_meta.json.gz'), 'rt', encoding='utf-8') as f:
    drg = json.load(f)
with gzip.open(os.path.join(base, 'icd10_map.json.gz'), 'rt', encoding='utf-8') as f:
    icd10 = json.load(f)
with gzip.open(os.path.join(base, 'icd9_map.json.gz'), 'rt', encoding='utf-8') as f:
    icd9 = json.load(f)

print('=== Building optimized coding rules ===')
rules = {}

# --- 1. Mutual exclusion (compact: code -> table names) ---
print('1. Mutual exclusion rules...')
mutex = {}
for tbl_name, codes in drg['excl'].items():
    if len(codes) < 2:
        continue
    for code in codes:
        if code not in mutex:
            mutex[code] = []
        mutex[code].append(tbl_name)

excl_tables = {}
for tbl_name, codes in drg['excl'].items():
    if len(codes) < 2:
        continue
    excl_tables[tbl_name] = {
        'codes': list(codes),
        'names': {c: icd10.get(c, {}).get('name', '') for c in codes if c in icd10}
    }

rules['mutual_exclusion'] = mutex
rules['exclusion_tables'] = excl_tables
print(f'   {len(mutex)} codes with exclusions, {len(excl_tables)} tables')

# --- 2. Combination codes (curated rules from ICD-10 Volume 2) ---
print('2. Combination code rules...')
combo_rules = {
    'hypertension_heart': {
        'desc': '高血压合并心脏病应合并编码为高血压心脏病(I11)',
        'triggers_prefix': ['I10.'],
        'when_with_prefix': ['I50.', 'I51.4', 'I51.5', 'I51.6', 'I51.7', 'I51.8'],
        'action': '主诊从I10改为I11.0(伴心衰)或I11.9(不伴心衰)',
        'source': 'ICD-10卷二 4.4.1'
    },
    'hypertension_renal': {
        'desc': '高血压合并慢性肾病应合并编码为高血压性肾病(I12)',
        'triggers_prefix': ['I10.'],
        'when_with_prefix': ['N18.'],
        'action': '主诊从I10改为I12.0(CKD5期)或I12.9(非CKD5期)',
        'source': 'ICD-10卷二 4.4.1'
    },
    'hypertension_heart_renal': {
        'desc': '高血压心脏病+肾病应用I13高血压性心肾病合并编码',
        'triggers_prefix': ['I11.', 'I12.'],
        'when_with_prefix': ['I50.', 'N18.'],
        'action': '主诊改为I13.0/I13.1/I13.2/I13.9',
        'source': 'ICD-10卷二 4.4.1'
    },
    'dm_renal': {
        'desc': '糖尿病+肾病应使用双重分类编码(E1x.2+N08.3*)',
        'triggers_prefix': ['E10.', 'E11.', 'E13.', 'E14.'],
        'when_with': ['N08.3'],
        'action': '使用糖尿病肾病联合编码，糖尿病为主编码',
        'source': 'ICD-10卷二 4.2'
    },
    'dm_ketoacidosis': {
        'desc': '糖尿病+酮症酸中毒应合并编码为E1x.1糖尿病伴酮症酸中毒',
        'triggers_prefix': ['E10.9', 'E11.9', 'E14.9'],
        'when_with': ['E87.2'],
        'action': '主诊改为E1x.1，取消E87.2',
        'source': 'ICD-10卷二 4.2'
    },
    'hernia_obstruction': {
        'desc': '疝+肠梗阻应合并编码为疝伴梗阻(同类目.3或.4)',
        'triggers_prefix': ['K40.', 'K41.', 'K42.', 'K43.', 'K44.', 'K45.', 'K46.'],
        'when_with': ['K56.6'],
        'action': '使用疝伴梗阻编码(K4x.3/K4x.4)，取消单独的肠梗阻编码',
        'source': 'ICD-10卷二 4.4.6'
    },
    'pneumonia_organism': {
        'desc': '肺炎(J18)有明确病原体时应用特异性肺炎编码(J15/J16)',
        'triggers_prefix': ['J18.'],
        'when_with_prefix': ['B95.', 'B96.'],
        'action': '主诊改为J15/J16特异性肺炎编码，附加B95/B96病原体编码',
        'source': 'ICD-10卷二 4.4.5'
    },
    'sepsis_shock': {
        'desc': '脓毒症(A40/A41)伴感染性休克应附加R65.1脓毒性休克',
        'triggers_prefix': ['A40.', 'A41.'],
        'when_with': ['R57.2'],
        'action': '附加编码R65.1(脓毒性休克)或R57.2(感染性休克)',
        'source': 'ICD-10卷二 4.4.10'
    },
    'cerebral_infarction_stenosis': {
        'desc': '脑梗死(I63)+脑血管狭窄/闭塞(I65/I66)应明确哪个为主要诊断',
        'triggers_prefix': ['I63.'],
        'when_with_prefix': ['I65.', 'I66.'],
        'action': '脑梗死作为主要诊断，脑血管狭窄作为其他诊断',
        'source': '中国脑血管病临床管理指南(2023)'
    },
    'chf_with_ht': {
        'desc': '心力衰竭(I50)不应用作主要诊断当有明确病因时',
        'triggers_prefix': ['I50.'],
        'when_with_prefix': ['I11.', 'I13.', 'I20-I25', 'I42.', 'I60-I69'],
        'action': '病因诊断作为主要诊断，心衰作为其他诊断',
        'source': 'ICD-10卷二 4.4.2'
    },
    'anemia_with_cause': {
        'desc': '贫血(D50-D64)有明确病因时应编码病因',
        'triggers_prefix': ['D50.', 'D51.', 'D52.', 'D53.', 'D61.', 'D62.', 'D63.', 'D64.'],
        'when_with_prefix': ['K92.', 'N92.', 'C', 'N18.'],
        'action': '病因诊断(如消化道出血/月经过多/CKD)作为主要诊断',
        'source': 'ICD-10卷二 4.4.4'
    },
}

# Build index: code -> matching rules
combo_index = {}
for rule_id, rule_def in combo_rules.items():
    for prefix in rule_def.get('triggers_prefix', []):
        for code in icd10:
            if code.startswith(prefix.rstrip('.')):
                info = {'rule_id': rule_id, 'desc': rule_def['desc'],
                        'when': rule_def.get('when_with', []) + rule_def.get('when_with_prefix', []),
                        'action': rule_def['action'], 'source': rule_def['source']}
                if code not in combo_index:
                    combo_index[code] = []
                combo_index[code].append(info)

rules['combination_codes'] = combo_rules
rules['combination_index'] = combo_index
print(f'   {len(combo_rules)} rule categories, {len(combo_index)} codes indexed')

# --- 3. Additional code rules ---
print('3. Additional code rules...')
addl_index = {}

for code, info in icd10.items():
    name = info.get('name', '')
    first_char = code[0] if code else ''

    # Injury/poisoning + external cause
    if first_char in 'ST' and len(code) > 1 and code[1].isdigit():
        if code not in addl_index:
            addl_index[code] = []
        addl_index[code].append({
            'desc': '损伤/中毒编码需附加外因编码(V01-Y98)说明致伤原因和地点',
            'add_category': '外因编码 V01-Y98',
            'source': 'ICD-10卷二 4.4.9'
        })

    # Neoplasm + morphology
    if first_char in 'CD' and code < 'D38' and len(code) > 1 and code[1].isdigit():
        if code not in addl_index:
            addl_index[code] = []
        addl_index[code].append({
            'desc': '肿瘤编码可附加形态学编码(M8000-M9989)说明病理类型',
            'add_category': '形态学编码 M8000-M9989',
            'source': 'ICD-10卷二 4.4.3'
        })

    # Infectious disease + organism
    if first_char == 'A' and code < 'B99' and len(code) > 1 and code[1].isdigit():
        if code not in addl_index:
            addl_index[code] = []
        addl_index[code].append({
            'desc': '感染性疾病可附加病原体耐药编码(B95-B98, U82-U84)',
            'add_category': '病原体编码 B95-B98 / 耐药编码 U82-U84',
            'source': 'ICD-10卷二 4.4.7'
        })

rules['additional_index'] = addl_index
print(f'   {len(addl_index)} codes with additional code rules')

# --- 4. Priority/main diagnosis rules ---
print('4. Priority coding rules...')
priority_rules = {
    'tumor_chemo': {
        'desc': '肿瘤患者入院行放/化疗时，Z51.x应作为主要诊断',
        'triggers_prefix': ['C', 'D0', 'D1', 'D2', 'D3'],
        'priority_rule': 'Z51.0(放疗)/Z51.1(化疗)/Z51.2(其他化疗)优先作为主要诊断，原肿瘤编码作为其他诊断',
        'source': '医保结算清单填写规范 第四部分(一)'
    },
    'obstetric_delivery': {
        'desc': '产科分娩编码(O80-O84)优先作为主要诊断',
        'triggers_prefix': ['O10-', 'O11-', 'O12-', 'O13-', 'O14-', 'O15-', 'O16-', 'O20-', 'O21-',
                          'O22-', 'O23-', 'O24-', 'O25-', 'O26-', 'O28-', 'O29-', 'O30-', 'O31-',
                          'O32-', 'O33-', 'O34-', 'O35-', 'O36-', 'O40-', 'O41-', 'O42-', 'O43-',
                          'O44-', 'O45-', 'O46-', 'O47-', 'O48-', 'O60-', 'O61-', 'O62-', 'O63-',
                          'O64-', 'O65-', 'O66-', 'O67-', 'O68-', 'O69-', 'O70-', 'O71-', 'O72-',
                          'O73-', 'O74-', 'O75-', 'O80-', 'O81-', 'O82-', 'O83-', 'O84-', 'O85-',
                          'O86-', 'O87-', 'O88-', 'O89-', 'O90-', 'O91-', 'O92-', 'O94-', 'O95-',
                          'O96-', 'O97-', 'O98-', 'O99-'],
        'priority_rule': 'O80-O84分娩编码优先作为主要诊断，产科并发症作为其他诊断',
        'source': '医保结算清单填写规范 第四部分(一)'
    },
    'suspected_diagnosis': {
        'desc': '疑似诊断(待查/待排/可能/?)不得填入医保结算清单',
        'priority_rule': '出院时仍为疑似状态的诊断不能作为任何编码填报',
        'source': '医保结算清单填写规范 第二部分(三)'
    },
    'postop_complication': {
        'desc': '术后并发症编码(T80-T88)需重点审核',
        'triggers_prefix': ['T80', 'T81', 'T82', 'T83', 'T84', 'T85', 'T86', 'T87', 'T88'],
        'priority_rule': '确认是否为医疗质量问题导致，作为其他诊断编码，可能影响DRG支付',
        'source': '医保结算清单填写规范'
    },
    'main_dx_selection': {
        'desc': '主要诊断选择原则：对健康危害最大、消耗资源最多、住院时间最长',
        'priority_rule': '1.主要治疗的疾病 2.三种情况并存时选最严重的 3.住院期间新发生的疾病优先于入院时已有',
        'source': 'ICD-10卷二 4.4; 医保结算清单填写规范'
    },
}

rules['priority_rules'] = priority_rules
print(f'   {len(priority_rules)} priority rules')

# --- 5. General coding principles ---
coding_principles = [
    {
        'id': 'specificity',
        'title': '编码特异性原则',
        'content': '应使用最特异的编码。有亚目时不用类目，有细目时不用亚目。避免使用".8"和".9"残余类目当有更特异的编码时。',
        'source': 'ICD-10卷二 3.2'
    },
    {
        'id': 'laterality',
        'title': '双侧性编码',
        'content': '双侧相同部位疾病：如存在专门的双侧编码则使用；否则分别编码左侧和右侧。',
        'source': 'ICD-10卷二 3.4'
    },
    {
        'id': 'acute_chronic',
        'title': '急慢性编码',
        'content': '同一疾病的急性和慢性同时存在时：如存在专门的合并编码(如J44慢阻肺急性加重)则使用；否则分别编码急性和慢性。',
        'source': 'ICD-10卷二 3.5'
    },
    {
        'id': 'sequelae',
        'title': '后遗症编码',
        'content': '后遗症/晚期效应的编码：使用B90-B94, E64, E68, G09, I69, O97, Y85-Y89等后遗症类目编码说明后遗症性质，另编码说明后遗症的具体表现。',
        'source': 'ICD-10卷二 4.4.8'
    },
    {
        'id': 'multiple_conditions',
        'title': '多情况编码',
        'content': '当多个情况都不能作为主要诊断时(B99, R69等)：选择对本次住院影响最大的那个情况作为主要诊断。避免使用"未特指"类编码作为主诊。',
        'source': 'ICD-10卷二 4.4.14'
    },
    {
        'id': 'symptom_vs_diagnosis',
        'title': '症状与确诊',
        'content': '有明确诊断时不应使用症状编码(如已确诊肺炎则不应编码"咳嗽R05")。症状编码仅在确实无法明确病因时使用。',
        'source': 'ICD-10卷二 4.4.11'
    },
]

rules['coding_principles'] = coding_principles
print(f'   {len(coding_principles)} general principles')

# --- Save ---
output = os.path.join(base, 'coding_rules.json')
with open(output, 'w', encoding='utf-8') as f:
    json.dump(rules, f, ensure_ascii=False)

with open(output, 'rb') as f:
    data = f.read()
with gzip.open(output + '.gz', 'wb', compresslevel=9) as f:
    f.write(data)

size = os.path.getsize(output)
gz_size = os.path.getsize(output + '.gz')
print(f'\nSaved: {output} ({size:,} bytes, gz: {gz_size:,} bytes)')
print('DONE')
