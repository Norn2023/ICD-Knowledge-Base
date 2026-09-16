"""
Tag drugs: 慢病, 特病, 精二
慢病=门诊慢性病 特病=门诊特殊病（国家规定范围不同）
"""
import json, sys, os, re, gzip

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))

# 国家规定: 慢病 vs 特病 范围
CHRONIC_DISEASES = {  # 慢病
    '高血压', '糖尿病', '冠心病', '慢性肝炎', '肝硬化',
    '类风湿关节炎', '帕金森病', '帕金森综合征',
    '慢性阻塞性肺疾病', '支气管哮喘', '肺心病',
    '阿尔茨海默病', '脑血管病后遗症', '癫痫',
    '慢性肾病', '肾病综合征', '甲状腺功能减退',
    '银屑病', '白癜风', '强直性脊柱炎',
}

SPECIAL_DISEASES = {  # 特病
    '恶性肿瘤', '器官移植', '尿毒症', '血友病',
    '再生障碍性贫血', '精神分裂症', '系统性红斑狼疮',
    '肺结核', '耐多药结核', '艾滋病',
    '白血病', '淋巴瘤', '骨髓瘤',
    '慢性粒细胞白血病', '真性红细胞增多症',
    '原发性血小板增多症', '骨髓纤维化',
    '血友病A', '血友病B', '血管性血友病',
}

PSYCHO_2_PATTERNS = [
    '西泮', '唑仑', '艾司唑', '阿普唑', '三唑仑', '咪达唑仑',
    '劳拉西泮', '奥沙西泮', '氯硝西泮', '硝西泮', '氟西泮',
    '夸西泮', '溴西泮', '氯甲西泮', '替马西泮', '氯卓酸',
    '巴比妥', '司可巴比妥', '戊巴比妥', '异戊巴比妥',
    '佐匹克隆', '唑吡坦', '扎来普隆', '右佐匹克隆',
    '曲马多', '可待因', '喷他佐辛', '布托啡诺', '纳布啡',
    '氨酚羟考酮', '氨酚曲马多', '哌甲酯', '氯胺酮', '甲丙氨酯',
    '丁丙诺啡透皮', '丁丙诺啡纳洛酮',
]

def classify_disease(name):
    """Classify disease as 慢病, 特病, or None"""
    if not name: return None
    for sd in SPECIAL_DISEASES:
        if sd in name: return '特病'
    for cd in CHRONIC_DISEASES:
        if cd in name: return '慢病'
    return None

def main():
    print("药品标签: 慢病/特病 + 精二")
    with open(os.path.join(BASE, 'drugs.json'), 'r', encoding='utf-8') as f:
        drugs = json.load(f)

    slow = 0; special = 0; psycho2 = 0

    for d in drugs:
        rx = d.get('prescribing', {})
        inds = rx.get('indications', [])

        # Remove old field
        for k in ['slow_disease', 'disease_type']:
            d.pop(k, None)

        # Determine disease type from indications
        disease_type = None
        for ind in inds:
            dt = None
            if ind.get('慢病'): dt = '慢病'
            elif ind.get('特病'): dt = '特病'
            if not dt: continue
            if disease_type and disease_type != dt:
                disease_type = '慢病+特病'
            else:
                disease_type = dt

        if disease_type:
            d['disease_type'] = disease_type
            if disease_type == '慢病': slow += 1
            elif disease_type == '特病': special += 1
            else: special += 1  # 慢病+特病 counts as both

        # 精二
        n = d.get('name', '')
        if any(pat in n for pat in PSYCHO_2_PATTERNS):
            d['psychotropic_2'] = True
            psycho2 += 1
        else:
            d.pop('psychotropic_2', None)

    print(f"  慢病: {slow}  特病: {special}  精二: {psycho2}")

    # Save
    with open(os.path.join(BASE, 'drugs.json'), 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, 'drugs.json'), 'rb') as f_in:
        with gzip.open(os.path.join(BASE, 'drugs.json.gz'), 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())

    # Samples
    for label in ['慢病', '特病']:
        for d in drugs:
            if d.get('disease_type') == label:
                rx = d.get('prescribing', {})
                inds = rx.get('indications', [])
                for ind in inds:
                    dt = ind.get('慢病') or ind.get('特病')
                    if dt:
                        print(f"  {label}: {d['name']} → {ind.get('text','')[:40]}...")
                        break
                break

    print(f"\n✅ 完成")

if __name__ == '__main__':
    main()
