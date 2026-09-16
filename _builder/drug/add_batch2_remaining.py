"""Add remaining batch 2 drugs to build_drug_info.py"""
import re

entries = r"""
    '门冬氨酸鸟氨酸': {
        'en_name': 'Ornithine Aspartate', 'category': '氨基酸制剂·肝性脑病用药', 'is_essential': False,
        'indications': [
            {'text': '用于急慢性肝病所致的高血氨症，尤其是肝性脑病的降氨治疗。', 'icd10': 'K72.900', 'offlabel': False},
        ],
        'dosage': ['口服：每次3g，每日2-3次', '静脉：5-20g/日，加入5%GS 250-500ml静滴，滴速≤5g/h'],
        'adverse_reactions': ['偶见恶心、呕吐'],
        'contraindications': ['严重肾功能不全（Cr>3mg/dL）', '氨基酸代谢异常'],
        'interactions': ['与利尿剂合用时注意电解质'],
        'special_populations': ['妊娠期：慎用', '肾功能不全：禁用严重者'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确高血氨症诊断依据（血氨>正常上限），肝性脑病须有意识障碍或扑翼样震颤等体征记录', 'materials': ['血氨检测报告', '肝性脑病分级评估记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈', 'materials': ['肝病专科病历', '门诊处方']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['门诊处方']},
        ],
        'other': ['主要用于降低血氨', '滴速不宜过快'],
    },

    '阿比特龙': {
        'en_name': 'Abiraterone Acetate', 'category': 'CYP17抑制剂·抗前列腺癌', 'is_essential': False,
        'indications': [
            {'text': '联合泼尼松用于转移性去势抵抗性前列腺癌（mCRPC）。', 'icd10': 'C61.x00', '特病': True, '特病名称': '前列腺癌', 'offlabel': False},
            {'text': '联合泼尼松+ADT用于高危转移性激素敏感性前列腺癌（mHSPC）。', 'icd10': 'C61.x00', '特病': True, '特病名称': '前列腺癌', 'offlabel': False},
        ],
        'dosage': ['1000mg qd 空腹口服（餐前≥1h或餐后≥2h），联合泼尼松5mg bid'],
        'adverse_reactions': ['高血压(37%)、低钾血症(28%)、外周水肿(25%)——盐皮质激素过量综合征', '肝毒性（ALT升高，监测肝功能）'],
        'contraindications': ['严重肝功能不全（Child-Pugh C级）', '妊娠或可能妊娠的妇女（禁用——女性不应接触本品）'],
        'interactions': ['CYP3A4强诱导剂（利福平）：降低阿比特龙疗效', 'CYP2D6底物（美托洛尔、普罗帕酮等）：阿比特龙可能增加其血药浓度'],
        'special_populations': ['妊娠期：女性禁用', '肝功能不全：Child-Pugh B级减量至250mg qd', '肾功能不全：无需调整'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有转移性前列腺癌（C61）明确诊断和去势治疗抵抗的证据（睾酮<50ng/dL+PSA进展或影像学进展）方可支付', 'materials': ['前列腺癌病理报告', 'PSA系列监测报告', '骨扫描/CT/MRI示转移灶']},
            {'risk': 'medium', 'text': '医保乙类·国谈，须每月监测肝功能（ALT/AST）和血钾', 'materials': ['肝功能+电解质监测报告（近1月）']},
            {'risk': 'medium', 'text': '须联合泼尼松使用，单用阿比特龙不合理', 'materials': ['联合泼尼松处方']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['空腹服用', '必须联合泼尼松（预防盐皮质激素过量）', '服药前后2h禁食'],
    },

    '地拉罗司': {
        'en_name': 'Deferasirox', 'category': '铁螯合剂', 'is_essential': False,
        'indications': [
            {'text': '用于因β-地中海贫血等输血依赖性贫血所致的慢性铁过载（血清铁蛋白>1000μg/L）。', 'icd10': 'D56.100', 'offlabel': False},
        ],
        'dosage': ['起始20mg/kg/日，根据铁蛋白水平调整，最大40mg/kg/日', '空腹服用，用前将药片溶于水/果汁中'],
        'adverse_reactions': ['胃肠道反应（腹泻、恶心）', '皮疹', '肾小管损害（蛋白尿）', '肝酶升高', '胃肠道出血（罕见但严重）'],
        'contraindications': ['肾功能不全（eGFR<60）', '活动性消化性溃疡'],
        'interactions': ['含铝抗酸剂：避免同时使用', 'CYP3A4代谢：注意相关药物相互作用'],
        'special_populations': ['儿童（≥2岁）：可用', '妊娠期：不推荐', '肾功能不全：禁用（eGFR<60）'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有输血依赖性贫血明确诊断+铁过载证据（铁蛋白>1000μg/L或肝铁浓度>3mg/g）', 'materials': ['贫血确诊记录', '血清铁蛋白检测报告（近3月）', '输血记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，须每月监测肾功能（Cr+eGFR）、尿蛋白和肝功能', 'materials': ['肾功能+尿蛋白+肝功能报告（近1月）']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['血液科专科处方']},
        ],
        'other': ['空腹服用', '药片分散于水/果汁中服用', '定期监测听力和眼科（少见不良反应）'],
    },

    '盐酸安罗替尼胶囊': {
        'en_name': 'Anlotinib', 'category': '多靶点TKI·抗肿瘤药', 'is_essential': False,
        'indications': [
            {'text': '用于既往至少接受过2种系统化疗后进展的晚期非小细胞肺癌（NSCLC）。', 'icd10': 'C34.900', '特病': True, '特病名称': '肺癌', 'offlabel': False},
            {'text': '用于既往至少接受过2种化疗方案后进展的小细胞肺癌（SCLC）。', 'icd10': 'C34.900', '特病': True, '特病名称': '肺癌', 'offlabel': False},
            {'text': '用于腺泡状软组织肉瘤、透明细胞肉瘤等软组织肉瘤的治疗。', 'icd10': 'C49.900', '特病': True, '特病名称': '软组织肉瘤', 'offlabel': False},
        ],
        'dosage': ['12mg qd×2周，停1周（3周为1周期）', '空腹口服', '根据不良反应可减至10mg或8mg qd'],
        'adverse_reactions': ['高血压（67%）', '手足综合征（皮肤反应，43%）', '蛋白尿（42%）', '甲状腺功能减退（36%）', '出血（3%，咳血/咯血需警惕）'],
        'contraindications': ['中央型肺鳞癌伴大咯血风险', '活动性出血', '严重高血压（未控制>150/100mmHg）'],
        'interactions': ['CYP3A4抑制剂/诱导剂：影响安罗替尼代谢', '抗凝/抗血小板药：增加出血风险'],
        'special_populations': ['妊娠期：禁用', '哺乳期：禁用', '肝功能不全：慎用', '高血压：控制血压后再用药'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有≥2线治疗后进展的明确记录，一线使用医保拒付；中央型肺鳞癌伴大咯血风险禁用', 'materials': ['既往治疗失败记录（≥2线）', '影像学进展报告', '病理报告（非鳞癌使用需谨慎）']},
            {'risk': 'medium', 'text': '医保乙类·国谈，每日监测血压，每周查尿常规（蛋白尿）', 'materials': ['血压监测记录', '尿常规报告（近1周）']},
            {'risk': 'medium', 'text': '用药2周停1周方案必须严格遵守', 'materials': ['用药周期记录']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['空腹服用', '2周用药+1周停药', '每日监测血压', '出现咯血立即停药就医'],
    },

    '曲普瑞林': {
        'en_name': 'Triptorelin', 'category': 'GnRH激动剂·激素治疗', 'is_essential': False,
        'indications': [
            {'text': '用于前列腺癌的去势治疗。', 'icd10': 'C61.x00', '特病': True, '特病名称': '前列腺癌', 'offlabel': False},
            {'text': '用于子宫内膜异位症的激素治疗。', 'icd10': 'N80.x00', 'offlabel': False},
            {'text': '用于中枢性性早熟的抑制治疗。', 'icd10': 'E22.800', 'offlabel': False},
        ],
        'dosage': ['前列腺癌：3.75mg或11.25mg IM q1-3M', '子宫内膜异位症：3.75mg IM q4w×6月', '性早熟：按体重50μg/kg q4w'],
        'adverse_reactions': ['潮热、多汗（去势效应）', '骨密度下降（长期使用）', '注射部位疼痛', '一过性睾酮升高（初始反跳，前列腺癌骨转移者需同时抗雄激素1-2周）'],
        'contraindications': ['妊娠及哺乳期', '未经诊断的阴道出血'],
        'interactions': ['与抗雄激素药物联用可减轻初始反跳效应'],
        'special_populations': ['妊娠期：禁用', '儿童：用于性早熟', '老年男性：前列腺癌长期使用注意骨密度'],
        'insurance_notes': [
            {'risk': 'high', 'text': '前列腺癌须有病理确诊；子宫内膜异位症须有腹腔镜或B超证据；中枢性性早熟须有GnRH激发试验证据', 'materials': ['前列腺癌病理报告/内异症诊断记录/GnRH激发试验报告']},
            {'risk': 'medium', 'text': '医保乙类·国谈，前列腺癌属特病，长期使用须监测骨密度', 'materials': ['骨密度检测报告（长期使用者）']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['专科处方']},
        ],
        'other': ['前列腺癌初始1-2周需联用抗雄激素防反跳', '长期使用建议补充钙剂和维生素D'],
    },

    '福莫特罗': {
        'en_name': 'Formoterol', 'category': 'LABA·长效β2受体激动剂', 'is_essential': False,
        'indications': [
            {'text': '用于支气管哮喘和COPD的长期维持治疗（需与吸入糖皮质激素联合使用）。', 'icd10': 'J45.900', '慢病': True, '慢病名称': '支气管哮喘', 'offlabel': False},
            {'text': '用于预防运动诱发的支气管痉挛。', 'icd10': 'J45.900', '慢病': True, '慢病名称': '支气管哮喘', 'offlabel': False},
        ],
        'dosage': ['吸入：每次4.5-9μg bid（仅在ICS+LABA合剂中作为组分使用）', '不可单独用于哮喘（增加哮喘相关死亡风险）'],
        'adverse_reactions': ['心悸、心动过速', '震颤', '低钾血症', '单药哮喘患者死亡率增加（FDA黑框警告）'],
        'contraindications': ['哮喘急性发作（不可替代急救用SABA）', '对福莫特罗过敏'],
        'interactions': ['β受体阻滞剂（包括滴眼液）：拮抗支气管扩张作用', '利尿剂、糖皮质激素：加重低钾'],
        'special_populations': ['妊娠期：慎用（宫缩抑制剂效应）', '老年人：无需调整'],
        'insurance_notes': [
            {'risk': 'high', 'text': '不可单药用于哮喘（增加死亡率），必须与ICS联合使用', 'materials': ['须与吸入糖皮质激素联合的处方']},
            {'risk': 'medium', 'text': '医保乙类·国谈，哮喘(J45)和COPD(J44)属门诊慢病', 'materials': ['呼吸专科确诊记录', '肺功能报告']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['门诊处方']},
        ],
        'other': ['必须与ICS联合使用（不可单用）', '起效快速（3-5分钟），可兼作急救使用'],
    },

    '妥布霉素': {
        'en_name': 'Tobramycin', 'category': '氨基糖苷类抗生素', 'is_essential': False,
        'indications': [
            {'text': '用于铜绿假单胞菌等敏感革兰阴性菌所致的重症感染（败血症、医院获得性肺炎、复杂性尿路感染）。', 'icd10': 'B96.500', 'offlabel': False},
            {'text': '用于囊性纤维化患者的慢性铜绿假单胞菌肺部感染（吸入剂型）。', 'icd10': 'E84.000', 'offlabel': False},
        ],
        'dosage': ['IV：3-6mg/kg/日，分3次', '吸入：300mg bid（囊性纤维化）', 'TDM监测：谷浓度<2mg/L，峰浓度4-10mg/L'],
        'adverse_reactions': ['肾毒性（发生率10-20%，剂量依赖性）', '耳毒性（不可逆，前庭/耳蜗损伤）', '神经肌肉阻滞（罕见）'],
        'contraindications': ['对氨基糖苷类过敏者', '重症肌无力'],
        'interactions': ['其他肾毒性/耳毒性药物（万古霉素、两性霉素B、顺铂、袢利尿剂）：增加毒性', '神经肌肉阻滞剂：增强阻滞效应'],
        'special_populations': ['妊娠期：可能致胎儿耳毒性（慎用）', '老年人：肾毒性风险增高', '肾功能不全：必须减量+TDM监测'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确铜绿假单胞菌或耐药革兰阴性菌感染的药敏证据；须TDM监测谷浓度（<2mg/L）', 'materials': ['药敏报告', '血药浓度监测结果（近3天）']},
            {'risk': 'medium', 'text': '医保乙类·国谈，疗程一般≤10-14天，超疗程须有病历记录', 'materials': ['肾功能监测记录', '疗程记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['感染科处方']},
        ],
        'other': ['TDM监测谷浓度（谷<2mg/L，峰4-10mg/L）', '充足水化减少肾毒性', '每日监测肾功能'],
    },

    '拉米夫定': {
        'en_name': 'Lamivudine', 'category': '核苷类似物·抗HBV/HIV', 'is_essential': False,
        'indications': [
            {'text': '用于慢性乙型肝炎（CHB）伴活动性肝病和/或ALT持续升高的抗病毒治疗。', 'icd10': 'B18.100', '慢病': True, '慢病名称': '慢性乙肝', 'offlabel': False},
            {'text': '用于HIV感染的联合抗逆转录病毒治疗（ART）的组成部分。', 'icd10': 'B24.x00', 'offlabel': False},
        ],
        'dosage': ['CHB：100mg qd', 'HIV：150mg bid或300mg qd（联合其他ART药物）', '肾功能不全：按eGFR调整'],
        'adverse_reactions': ['一般耐受性好', '乳酸酸中毒（罕见，核苷类似物类效应）', '停药后乙肝急性加重'],
        'contraindications': ['对拉米夫定过敏者'],
        'interactions': ['含恩曲他滨的制剂：不可重复使用（均为胞嘧啶类似物）', '甲氧苄啶/磺胺甲噁唑：增加拉米夫定血药浓度'],
        'special_populations': ['妊娠期：可用（FDA C类）', '哺乳期：可用', '儿童：可用', '肾功能不全：按eGFR调整'],
        'insurance_notes': [
            {'risk': 'high', 'text': 'CHB须有HBV-DNA阳性+ALT升高记录；HIV须有HIV-RNA+CD4检测', 'materials': ['HBV-DNA/HIV-RNA检测报告', '肝功/CD4报告']},
            {'risk': 'medium', 'text': '医保乙类·国谈，慢性乙肝属门诊慢病', 'materials': ['感染科/肝病专科确诊记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['专科处方']},
        ],
        'other': ['不可擅自停药（停药可致乙肝急性加重）', '长期治疗需定期监测'],
    },

    '伊立替康': {
        'en_name': 'Irinotecan', 'category': '拓扑异构酶Ⅰ抑制剂·抗肿瘤', 'is_essential': False,
        'indications': [
            {'text': '用于转移性结直肠癌的一线及后线化疗（联合5-FU/LV或单药）。', 'icd10': 'C18.900', '特病': True, '特病名称': '结直肠癌', 'offlabel': False},
        ],
        'dosage': ['FOLFIRI方案：180mg/m² IV q2w', '单药：350mg/m² IV q3w', 'UGT1A1基因多态性患者（*28/*28纯合子）：起始剂量减量'],
        'adverse_reactions': ['迟发性腹泻（用药24h后，发生率80%，严重者可致死——须立即使用洛哌丁胺）', '急性胆碱能综合征（早发性腹泻+出汗+腹痛，阿托品治疗）', '骨髓抑制（中性粒细胞减少，剂量限制性毒性）'],
        'contraindications': ['严重骨髓抑制', '对伊立替康过敏者'],
        'interactions': ['CYP3A4诱导剂（苯妥英、卡马西平）：降低伊立替康疗效', '酮康唑：增加伊立替康毒性'],
        'special_populations': ['妊娠期：禁用', 'UGT1A1*28纯合子：起始减量', '肝功能不全：胆红素升高者减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有结直肠癌（C18/C20）病理确诊；每次用药前须查血常规（中性粒细胞≥1.5×10⁹/L方可化疗）', 'materials': ['结直肠癌病理报告', '化疗前血常规（中性粒细胞计数）']},
            {'risk': 'high', 'text': 'UGT1A1基因检测推荐（*28纯合子起始减量防严重毒性）', 'materials': ['UGT1A1基因型报告（如有）']},
            {'risk': 'medium', 'text': '医保乙类·国谈，化疗期间须住院或日间病房监护（迟发性腹泻风险）', 'materials': ['化疗方案记录', '化疗监护记录']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['迟发性腹泻：立即口服洛哌丁胺4mg+每2h 2mg直至腹泻停止12h', '急性胆碱能综合征：阿托品0.25-1mg皮下', '化疗期间避免使用泻药和促进肠蠕动药'],
    },

    '舒马普坦': {
        'en_name': 'Sumatriptan', 'category': '5-HT1B/1D受体激动剂·抗偏头痛', 'is_essential': False,
        'indications': [
            {'text': '用于急性偏头痛发作（伴或不伴先兆）的对症治疗。', 'icd10': 'G43.900', 'offlabel': False},
            {'text': '用于丛集性头痛的急性治疗（皮下注射剂型）。', 'icd10': 'G44.000', 'offlabel': False},
        ],
        'dosage': ['口服：50-100mg，头痛发作时服用，2h后可重复（最大300mg/日）', '皮下：6mg，1h后可重复（最大12mg/日）', '鼻喷：10-20mg，2h后可重复'],
        'adverse_reactions': ['胸部压迫感/沉重感（发生率5%，非心源性）', '注射部位反应（皮下剂型）', '恶心、头晕、乏力'],
        'contraindications': ['冠心病、变异型心绞痛、既往心梗', '未控制的高血压', '脑血管意外/TIA史', '偏瘫型或基底型偏头痛', 'MAOI联用或MAOI停药2周内'],
        'interactions': ['MAOI：绝对禁忌（5-HT综合征风险）', '麦角胺：24h内避免合用（血管痉挛叠加）', 'SSRI/SNRI：可能增加5-HT综合征风险'],
        'special_populations': ['妊娠期：慎用', '哺乳期：用药后12h停止哺乳', '老年人：心血管评估后再用', '肝功能不全：减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '冠心病/脑血管疾病史者禁用；首次使用建议在医疗机构内观察30分钟', 'materials': ['心血管病史筛查记录', '首次使用观察记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，偏头痛须专科确诊并排除其他头痛原因', 'materials': ['神经内科确诊记录', '头痛日记/发作频率记录']},
            {'risk': 'medium', 'text': '每月使用≤10天（避免药物过量性头痛MOH）', 'materials': ['用药频率记录（≤10天/月）']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['神经内科处方']},
        ],
        'other': ['头痛发作时尽早服用（越早效果越好）', '每月使用不超过10天防MOH', '冠心病风险者用药前须排除'],
    },

    '注射用奥马珠单抗': {
        'en_name': 'Omalizumab', 'category': '抗IgE单克隆抗体·哮喘用药', 'is_essential': False,
        'indications': [
            {'text': '用于中重度持续性过敏性哮喘（经ICS+LABA治疗后仍控制不佳，IgE水平符合治疗范围）。', 'icd10': 'J45.900', '慢病': True, '慢病名称': '支气管哮喘', 'offlabel': False},
            {'text': '用于慢性自发性荨麻疹（CSU）对H1抗组胺药治疗无效的附加治疗。', 'icd10': 'L50.800', 'offlabel': False},
            {'text': '用于慢性鼻窦炎伴鼻息肉（CRSwNP）对鼻用激素治疗反应不佳的附加治疗。', 'icd10': 'J33.900', 'offlabel': True, 'offlabel_source': 'FDA批准扩展适应症'},
        ],
        'dosage': ['哮喘：150-375mg SC q2-4w（根据基线IgE水平和体重计算）', 'CSU：300mg SC q4w', '须在医疗机构内注射，观察过敏反应'],
        'adverse_reactions': ['注射部位反应（最常见）', '速发过敏反应（发生率0.1-0.2%），用药后观察30分钟', '寄生虫感染风险轻微增加'],
        'contraindications': ['对奥马珠单抗过敏者', '哮喘急性加重或支气管痉挛状态'],
        'interactions': ['无已知的药物相互作用'],
        'special_populations': ['妊娠期：权衡利弊', '哺乳期：慎用', '儿童（≥6岁）：可用', 'IgE>1500IU/mL或体重超出剂量表范围：不适用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '过敏性哮喘须满足：IgE 30-1500IU/mL+ICS+LABA控制不佳+明确的过敏原致敏证据（皮肤点刺或sIgE阳性）；不满足任一条件医保拒付', 'materials': ['IgE检测报告', '过敏原检测报告', 'ICS+LABA治疗失败的病历记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，哮喘属门诊慢病；每次注射后观察30分钟（速发过敏反应）', 'materials': ['注射后观察记录']},
            {'risk': 'low', 'text': '医保乙类·国谈，须在医疗机构内注射', 'materials': ['呼吸科/变态反应科处方']},
        ],
        'other': ['根据IgE水平+体重计算剂量', '注射后观察至少30分钟', '不可突然替代口服激素'],
    },

    '特瑞普利单抗注射液': {
        'en_name': 'Toripalimab', 'category': 'PD-1抑制剂·免疫检查点抑制剂', 'is_essential': False,
        'indications': [
            {'text': '用于既往全身治疗失败的不可切除或转移性黑色素瘤。', 'icd10': 'C43.900', '特病': True, '特病名称': '黑色素瘤', 'offlabel': False},
            {'text': '用于含铂化疗失败的局部晚期或转移性尿路上皮癌。', 'icd10': 'C67.900', '特病': True, '特病名称': '尿路上皮癌', 'offlabel': False},
            {'text': '用于复发/转移性鼻咽癌的一线及后线治疗。', 'icd10': 'C11.900', '特病': True, '特病名称': '鼻咽癌', 'offlabel': False},
        ],
        'dosage': ['3mg/kg IV q2w或240mg IV q3w', '静脉输注≥60分钟（首次）→≥30分钟（耐受良好者）'],
        'adverse_reactions': ['免疫相关性肺炎（3.5%）', '免疫相关性肝炎', '免疫相关性皮炎/结肠炎', '内分泌异常（甲减/甲亢/肾上腺皮质功能不全/1型糖尿病）', '输液反应'],
        'contraindications': ['活动性自身免疫性疾病', '脏器移植术后', '对PD-1抑制剂过敏者'],
        'interactions': ['糖皮质激素（>10mg泼尼松等效剂量）：可能降低免疫治疗疗效', '免疫抑制剂：可能拮抗疗效'],
        'special_populations': ['妊娠期：禁用', '哺乳期：不推荐', '肝功能不全：慎用', '自身免疫病：慎用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确的适应症病理确诊+既往治疗失败记录；黑色素瘤须有BRAF检测（靶向治疗优先选择）', 'materials': ['病理报告', '既往治疗失败记录', 'BRAF基因检测报告（黑色素瘤）']},
            {'risk': 'medium', 'text': '医保乙类·国谈，每次用药前评估免疫相关不良反应（皮肤/肺/肝/内分泌）', 'materials': ['免疫相关不良反应评估记录', '甲功/肝功/肺功能监测']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['免疫相关不良反应可累及任何器官', '治疗期间及停药后5月避孕', '出现≥3级irAE永久停药'],
    },

    '万古霉素': {
        'en_name': 'Vancomycin', 'category': '糖肽类抗生素·抗MRSA', 'is_essential': False,
        'indications': [
            {'text': '用于MRSA等耐药革兰阳性菌所致的重症感染（败血症、感染性心内膜炎、医院获得性肺炎等）。', 'icd10': 'A41.900', 'offlabel': False},
            {'text': '用于伪膜性肠炎（艰难梭菌感染，甲硝唑治疗失败或重症时口服万古霉素）。', 'icd10': 'A04.700', 'offlabel': False},
        ],
        'dosage': ['IV：15-20mg/kg q8-12h（根据体重和肾功能）', '口服（仅伪膜性肠炎）：125mg q6h×10天', 'TDM：谷浓度10-20mg/L（重症15-20）', '滴注时间≥60分钟（预防红人综合征）'],
        'adverse_reactions': ['肾毒性（谷浓度>20mg/L发生率增高）', '耳毒性（少见，高浓度时）', '红人综合征（快速输注引起组胺释放：面部/躯干红疹+低血压）'],
        'contraindications': ['对万古霉素过敏者'],
        'interactions': ['氨基糖苷类、两性霉素B、顺铂：增加肾毒性', '麻醉药：增加红人综合征风险'],
        'special_populations': ['妊娠期：可用（口服不吸收）', '肾功能不全：严格TDM减量', '老年人：肾毒性风险高'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有MRSA药敏证据或重症革兰阳性菌感染经验性治疗指征；必须TDM监测谷浓度>10mg/L', 'materials': ['MRSA药敏报告或经验性治疗指征记录', '血药谷浓度监测结果']},
            {'risk': 'medium', 'text': '医保乙类·国谈，疗程须记录，口服仅限伪膜性肠炎', 'materials': ['肾功能监测记录', '疗程记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['感染科处方']},
        ],
        'other': ['必须TDM监测谷浓度', '输注时间≥60分钟防红人综合征', '每日监测肾功能'],
    },

    '咪达唑仑': {
        'en_name': 'Midazolam', 'category': '苯二氮卓类·镇静/麻醉用药', 'is_essential': False,
        'indications': [
            {'text': '用于麻醉前用药、诊断或治疗操作前的清醒镇静。', 'icd10': 'Z51.800', 'offlabel': False},
            {'text': '用于ICU患者的长时程镇静。', 'icd10': 'F05.900', 'offlabel': False},
            {'text': '用于癫痫持续状态的紧急治疗（作为二线药物）。', 'icd10': 'G41.900', 'offlabel': False},
        ],
        'dosage': ['清醒镇静：初始2-2.5mg IV（老年人1-1.5mg），缓慢推注', 'ICU镇静：负荷0.03-0.3mg/kg，维持0.03-0.2mg/kg/h', '癫痫持续状态：10mg IM或0.2mg/kg IM（院前急救）'],
        'adverse_reactions': ['呼吸抑制/呼吸暂停（与阿片类联用或快速推注时风险显著增加）', '低血压', '顺行性遗忘', '反常反应（激越、攻击行为——儿童/老年人多见）'],
        'contraindications': ['严重呼吸功能不全', '睡眠呼吸暂停综合征未经治疗', '重症肌无力'],
        'interactions': ['CYP3A4抑制剂（酮康唑、克拉霉素、利托那韦）：显著升高咪达唑仑血药浓度', '阿片类：增强呼吸抑制', '酒精：增强中枢抑制'],
        'special_populations': ['妊娠期：慎用（分娩前使用可致新生儿呼吸抑制）', '老年人：减量使用（1-1.5mg起始），CYP3A4代谢下降', '肥胖：按理想体重给药'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须在具备呼吸支持和急救条件的医疗环境下使用', 'materials': ['麻醉/ICU操作记录', '血氧+血压监测记录']},
            {'risk': 'medium', 'text': '医保甲类·国谈，为麻醉药品管控药物', 'materials': ['麻醉/ICU处方']},
            {'risk': 'low', 'text': '医保甲类·国谈', 'materials': ['处方']},
        ],
        'other': ['须在监护条件下使用', '与阿片类联用呼吸抑制风险倍增', '老年人起始剂量减半'],
    },

    '注射用阿替普酶': {
        'en_name': 'Alteplase (rt-PA)', 'category': '溶栓药·纤溶酶原激活剂', 'is_essential': False,
        'indications': [
            {'text': '用于急性缺血性脑卒中（发病≤4.5h，符合溶栓适应症）的溶栓治疗。', 'icd10': 'I63.900', 'offlabel': False},
            {'text': '用于急性ST段抬高型心肌梗死（STEMI，发病≤12h）的溶栓治疗。', 'icd10': 'I21.900', 'offlabel': False},
            {'text': '用于急性大面积肺栓塞伴血流动力学不稳定的溶栓治疗。', 'icd10': 'I26.900', 'offlabel': False},
        ],
        'dosage': ['脑梗死：0.9mg/kg（最大90mg），先10%团注→余量60min输注', 'STEMI：15mg团注→50mg/30min→35mg/60min（100mg/90min方案）', '肺栓塞：100mg 2h输注'],
        'adverse_reactions': ['颅内出血（脑梗死溶栓发生率6.4%）', '全身性出血', '过敏反应', '再灌注心律失常（心梗溶栓时）'],
        'contraindications': ['活动性内出血', '近期颅内手术或严重头部外伤', '既往颅内出血史', '主动脉夹层', '不可压迫部位的大血管穿刺'],
        'interactions': ['抗凝药、抗血小板药：增加出血风险', 'ACEI：增加过敏反应'],
        'special_populations': ['妊娠期：权衡利弊（出血风险）', '老年人（>80岁）：脑梗死溶栓慎用，>3h需影像筛选'],
        'insurance_notes': [
            {'risk': 'high', 'text': '脑梗死溶栓必须严格遵守≤4.5h时间窗；须CT排除出血；须NIHSS评估（≥4分）', 'materials': ['颅脑CT（排除出血）', '发病时间记录（精确到分钟）', 'NIHSS评分记录']},
            {'risk': 'high', 'text': '出血性卒中、近期手术/外伤、活动性出血者绝对禁忌', 'materials': ['出血禁忌症筛查记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，须在卒中中心或有溶栓资质的医疗机构使用', 'materials': ['知情同意书', '溶栓监护记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['卒中中心处方']},
        ],
        'other': ['脑梗死溶栓：4.5h内黄金时间窗', '溶栓后24h内禁用抗血小板/抗凝药', '溶栓后24h复查CT排除出血转化'],
    },

    '注射用尤瑞克林': {
        'en_name': 'Urinary Kallidinogenase', 'category': '脑血管病用药·激肽释放酶', 'is_essential': False,
        'indications': [
            {'text': '用于急性缺血性脑卒中（轻中度），改善脑侧支循环和神经功能预后。', 'icd10': 'I63.900', 'offlabel': False},
        ],
        'dosage': ['0.15 PNA单位溶于100ml NS，IV 30min，qd×14天'],
        'adverse_reactions': ['一过性低血压（滴注时发生率约5%）', '头晕、恶心', '偶见过敏反应'],
        'contraindications': ['脑出血', '严重低血压（SBP<90mmHg）'],
        'interactions': ['ACEI：尤瑞克林为激肽释放酶，ACEI可增强其降压效应——联用时需监测血压'],
        'special_populations': ['妊娠期：尚无数据', '低血压：不建议使用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有急性缺血性脑卒中（I63）颅脑CT/MRI明确诊断；脑出血或低血压（SBP<90mmHg）禁用', 'materials': ['颅脑CT/MRI报告', '血压监测记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，疗程14天，须在发病48h内开始使用', 'materials': ['发病时间记录', '疗程记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['神经内科处方']},
        ],
        'other': ['滴注时监测血压（低血压反应）', '14天为一疗程'],
    },

    '帕洛诺司琼': {
        'en_name': 'Palonosetron', 'category': '5-HT3受体拮抗剂·长效止吐', 'is_essential': False,
        'indications': [
            {'text': '用于中重度致吐性化疗方案（MEC/HEC）所致的急性和迟发性恶心呕吐的预防。半衰期40h，对迟发性CINV效果优于第一代5-HT3拮抗剂。', 'icd10': 'R11.x00', '特病': True, '特病名称': '恶性肿瘤化疗', 'offlabel': False},
        ],
        'dosage': ['化疗前30min：0.25mg IV（单次）', '口服：0.5mg qd×化疗前1h，每日1次'],
        'adverse_reactions': ['头痛（9%）', '便秘（5%）', '头晕', 'QTc间期延长（与昂丹司琼类似，但风险较低）'],
        'contraindications': ['对帕洛诺司琼过敏者'],
        'interactions': ['其他延长QTc的药物（谨慎联用）', 'SSRI：可能增加5-HT综合征风险'],
        'special_populations': ['妊娠期：慎用', '老年：无需调整', '肝功能不全：无需调整'],
        'insurance_notes': [
            {'risk': 'high', 'text': '限化疗患者使用（HEC/MEC方案），非化疗场景（术后恶心呕吐、妊娠呕吐）医保拒付', 'materials': ['化疗方案记录', '化疗医嘱']},
            {'risk': 'medium', 'text': '医保乙类·国谈，化疗单次使用（0.25mg/次）', 'materials': ['化疗日处方']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['肿瘤科处方']},
        ],
        'other': ['半衰期40h（优于昂丹司琼3-6h）', '化疗前30min单次给药', '对迟发性CINV效果较好'],
    },

    '利多卡因': {
        'en_name': 'Lidocaine', 'category': '局部麻醉药/抗心律失常药', 'is_essential': False,
        'indications': [
            {'text': '用于局部浸润麻醉、神经阻滞、硬膜外麻醉。', 'icd10': 'Z51.800', 'offlabel': False},
            {'text': '用于室性心律失常（室性早搏、室性心动过速）的紧急治疗。', 'icd10': 'I47.200', 'offlabel': False},
        ],
        'dosage': ['局麻：1-2%溶液，最大4.5mg/kg（不含肾上腺素）或7mg/kg（含肾上腺素）', '抗心律失常：1-1.5mg/kg IV团注→1-4mg/min维持'],
        'adverse_reactions': ['中枢神经毒性（口周麻木→耳鸣→嗜睡→惊厥）', '心脏毒性（PR延长→QRS增宽→窦性停搏）', '过敏反应（罕见）'],
        'contraindications': ['Adams-Stokes综合征', '严重窦房/房室传导阻滞（无起搏器）'],
        'interactions': ['β受体阻滞剂：减少肝血流，升高利多卡因血药浓度', '西咪替丁：降低利多卡因清除'],
        'special_populations': ['妊娠期：可用（局麻）', '肝功能不全：减量', '心衰：减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '抗心律失常使用须有心电图监测；局麻药物中毒须具备急救条件（脂肪乳剂）', 'materials': ['心电图监测记录']},
            {'risk': 'medium', 'text': '医保甲类·国谈', 'materials': ['处方']},
            {'risk': 'low', 'text': '医保甲类·国谈', 'materials': ['处方']},
        ],
        'other': ['局麻用量不超过最大安全剂量', '抗心律失常用法需TDM监测'],
    },

    '氨磺必利': {
        'en_name': 'Amisulpride', 'category': '非典型抗精神病药', 'is_essential': False,
        'indications': [
            {'text': '用于精神分裂症（阳性和阴性症状均有效）。', 'icd10': 'F20.900', '特病': True, '特病名称': '精神分裂症', 'offlabel': False},
        ],
        'dosage': ['阴性症状为主：50-300mg/日', '阳性症状为主：400-800mg/日，最大1200mg/日'],
        'adverse_reactions': ['锥体外系反应（EPS，剂量依赖性）', '催乳素升高（明显，可致溢乳/闭经/性功能障碍）', '体重增加（比利培酮/奥氮平等少）', 'QTc间期延长（高剂量时）'],
        'contraindications': ['催乳素依赖性肿瘤（如垂体泌乳素瘤）', '嗜铬细胞瘤', '严重肾功能不全（CCr<10）'],
        'interactions': ['延长QTc的药物（避免联用）', '左旋多巴：拮抗抗帕金森效应'],
        'special_populations': ['妊娠期：慎用', '肾功能不全：CCr 30-60减量50%；10-30减量67%'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有精神分裂症（F20）精神专科确诊方可支付，其他精神障碍使用医保拒付', 'materials': ['精神专科确诊记录', 'PANSS评分']},
            {'risk': 'medium', 'text': '医保乙类·国谈，精神分裂症属门诊特病，须定期监测催乳素和心电图', 'materials': ['催乳素+ECG监测报告']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['精神科处方']},
        ],
        'other': ['对阴性症状效果较好', '高催乳素血症发生率较高', '肾功能不全必须减量'],
    },

    '依洛尤单抗注射液': {
        'en_name': 'Evolocumab', 'category': 'PCSK9抑制剂·降脂药', 'is_essential': False,
        'indications': [
            {'text': '用于经他汀最大耐受量治疗后LDL-C仍不达标的杂合子家族性高胆固醇血症（HeFH）或纯合子FH（HoFH）。', 'icd10': 'E78.000', 'offlabel': False},
            {'text': '用于他汀不耐受的动脉粥样硬化性心血管疾病（ASCVD）成人患者的LDL-C降低。', 'icd10': 'I25.101', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
        ],
        'dosage': ['140mg SC q2w或420mg SC q4w（腹部、大腿或上臂）'],
        'adverse_reactions': ['注射部位反应（6%）', '鼻咽炎（4%）', '上呼吸道感染'],
        'contraindications': ['对依洛尤单抗过敏者'],
        'interactions': ['与他汀类联用安全（协同降LDL-C）'],
        'special_populations': ['妊娠期：不推荐', '哺乳期：不推荐', '儿童（≥12岁HoFH）：可用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有他汀最大耐受量治疗≥3月后LDL-C仍不达标（ASCVD患者LDL-C>1.8mmol/L或FH患者>2.6mmol/L）的记录方可支付', 'materials': ['他汀治疗记录（≥3月）', '近3月血脂四项报告', 'ASCVD/FH诊断记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，冠心病(I25)属门诊慢病', 'materials': ['心内科/内分泌科专科确诊记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['专科处方']},
        ],
        'other': ['皮下注射，2-4周1次', '2-8℃冷藏保存', '他汀降脂基础上联用LDL-C可再降50-60%'],
    },

    '盐酸埃克替尼片': {
        'en_name': 'Icotinib', 'category': 'EGFR-TKI·抗肿瘤药（国产）', 'is_essential': False,
        'indications': [
            {'text': '用于EGFR敏感突变（19del/21 L858R）的局部晚期或转移性NSCLC的一线治疗。', 'icd10': 'C34.900', '特病': True, '特病名称': '肺癌', 'offlabel': False},
        ],
        'dosage': ['125mg tid 空腹或餐后口服'],
        'adverse_reactions': ['皮疹（痤疮样皮疹，发生率40-60%）', '腹泻（30-40%）', '肝酶升高', '间质性肺病（ILD，发生率<1%但可致死）'],
        'contraindications': ['对埃克替尼过敏者'],
        'interactions': ['CYP3A4抑制剂/诱导剂：影响代谢', '抑酸药（PPI/H2RA）：降低埃克替尼吸收（pH依赖性）'],
        'special_populations': ['妊娠期：不推荐', '肝功能不全：监测肝酶'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有EGFR敏感突变（19del/21 L858R）检测阳性的病理报告方可支付', 'materials': ['EGFR基因检测报告（19del或L858R阳性）', 'NSCLC病理报告']},
            {'risk': 'medium', 'text': '医保乙类·国谈，注意皮疹和腹泻的管理；新出现呼吸困难须警惕ILD', 'materials': ['皮肤+消化道不良反应评估记录']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['国产首创EGFR-TKI', '与抑酸药间隔≥2h服用', '出现新发呼吸困难须立即排查ILD'],
    },

    '维莫非尼片': {
        'en_name': 'Vemurafenib', 'category': 'BRAF抑制剂·抗肿瘤靶向药', 'is_essential': False,
        'indications': [
            {'text': '用于BRAF V600E突变的不可切除或转移性黑色素瘤的治疗。', 'icd10': 'C43.900', '特病': True, '特病名称': '黑色素瘤', 'offlabel': False},
        ],
        'dosage': ['960mg bid（空腹或餐后均可）'],
        'adverse_reactions': ['皮肤鳞状细胞癌/角化棘皮瘤（发生率20-25%，BRAF抑制剂的矛盾激活效应——须定期皮肤检查）', '关节痛/肌痛', '光敏反应（严重，须严格防晒）', 'QTc延长', '肝毒性'],
        'contraindications': ['对维莫非尼过敏者'],
        'interactions': ['CYP1A2底物（咖啡因、茶碱）：维莫非尼可升高其血药浓度', '延长QTc的药物：避免联用'],
        'special_populations': ['妊娠期：不推荐', '哺乳期：不推荐'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有BRAF V600E突变检测阳性的病理报告方可支付；须每2-3月进行全身皮肤检查（继发皮肤恶性肿瘤风险）', 'materials': ['BRAF V600E检测报告', '黑色素瘤病理报告', '皮肤科检查记录（定期）']},
            {'risk': 'medium', 'text': '医保乙类·国谈，日光暴露须严格防护', 'materials': ['光敏反应告知记录']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['严格防晒（严重光敏反应）', '定期全身皮肤检查（皮肤恶性肿瘤风险）', '与MEK抑制剂联用可减少皮肤毒性'],
    },

    '盐酸阿来替尼胶囊': {
        'en_name': 'Alectinib', 'category': 'ALK抑制剂·第二代', 'is_essential': False,
        'indications': [
            {'text': '用于ALK阳性局部晚期或转移性NSCLC的一线治疗及克唑替尼进展后的治疗。', 'icd10': 'C34.900', '特病': True, '特病名称': '肺癌', 'offlabel': False},
        ],
        'dosage': ['600mg bid 随餐口服（高脂餐增加吸收）'],
        'adverse_reactions': ['便秘（34%）', '肌痛/CPK升高（29%）', '外周水肿', '心动过缓（8%）', '间质性肺病（罕见）'],
        'contraindications': ['对阿来替尼过敏者'],
        'interactions': ['CYP3A4底物（如咪达唑仑）：阿来替尼可能影响其代谢', '心动过缓药物（β阻滞剂、地尔硫卓等）：叠加心动过缓效应'],
        'special_populations': ['妊娠期：不推荐', '肝功能不全：Child-Pugh C级减量至450mg bid'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有ALK融合基因检测阳性的病理报告方可支付', 'materials': ['ALK融合基因检测报告', 'NSCLC病理报告']},
            {'risk': 'medium', 'text': '医保乙类·国谈，CNS穿透性佳（优于克唑替尼，脑转移患者获益）', 'materials': ['脑MRI（脑转移评估）']},
            {'risk': 'low', 'text': '医保乙类·国谈，恶性肿瘤属门诊特病', 'materials': ['肿瘤专科处方']},
        ],
        'other': ['随餐服用（高脂餐增加生物利用度）', 'CNS穿透良好（脑转移一线TKI）', '监测CPK和心率'],
    },

    '硫培非格司亭注射液': {
        'en_name': 'Mecapegfilgrastim', 'category': 'G-CSF·升白细胞药', 'is_essential': False,
        'indications': [
            {'text': '用于非髓性恶性肿瘤化疗引起的中性粒细胞减少症，降低发热性中性粒细胞减少（FN）的发生率。', 'icd10': 'D70.x00', '特病': True, '特病名称': '恶性肿瘤化疗', 'offlabel': False},
        ],
        'dosage': ['化疗后24-48h：6mg SC（单次/化疗周期）', '不可在化疗前14天至化疗后24h内使用'],
        'adverse_reactions': ['骨痛（发生率20-30%，NSAID/对乙酰氨基酚对症处理）', '注射部位反应', '脾破裂（罕见但危及生命）', '急性呼吸窘迫综合征（罕见）'],
        'contraindications': ['对G-CSF过敏者', '化疗前14天内使用'],
        'interactions': ['锂盐：可能增强中性粒细胞释放效应'],
        'special_populations': ['妊娠期：慎用', '儿童：可用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有化疗记录+中性粒细胞减少（ANC<1.0×10⁹/L或预期FN>20%的化疗方案）', 'materials': ['化疗方案记录', 'ANC检测报告', 'FN风险评估（化疗方案FN发生率）']},
            {'risk': 'medium', 'text': '医保乙类·国谈，每化疗周期限用1次（6mg SC）', 'materials': ['化疗周期记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['肿瘤科处方']},
        ],
        'other': ['化疗后24-48h单次使用', '不可在化疗前14天内使用（可能加重骨髓抑制）', '骨痛为最常见的副作用'],
    },

    '地塞米松玻璃体内植入剂': {
        'en_name': 'Dexamethasone Intravitreal Implant', 'category': '糖皮质激素缓释植入剂·眼科', 'is_essential': False,
        'indications': [
            {'text': '用于视网膜静脉阻塞（RVO）的黄斑水肿。', 'icd10': 'H34.800', 'offlabel': False},
            {'text': '用于糖尿病性黄斑水肿（DME）。', 'icd10': 'E11.301', '慢病': True, '慢病名称': '糖尿病', 'offlabel': False},
            {'text': '用于非感染性葡萄膜炎的后段炎症。', 'icd10': 'H30.900', 'offlabel': False},
        ],
        'dosage': ['玻璃体内植入1支（0.7mg），药效持续3-6个月', '重复注射间隔≥3个月'],
        'adverse_reactions': ['眼压升高（发生率25-30%，通常一过性）', '白内障进展加速', '玻璃体出血', '眼内炎（罕见，<0.1%）', '植入物移位'],
        'contraindications': ['活动性或可疑眼部感染', '青光眼（未控制）', '后囊膜破裂'],
        'interactions': ['全身使用NSAID或抗凝药：增加玻璃体出血风险'],
        'special_populations': ['妊娠期：不推荐', '单眼患者：慎用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有RVO或DME或葡萄膜炎的确诊记录+OCT显示黄斑水肿；每眼累计≤5支，每年≤2支；须三级医院眼科或二级眼科专科处方；首次处方时矫正视力0.05-0.5', 'materials': ['OCT报告（黄斑水肿）', '矫正视力记录（0.05-0.5）', '三级医院眼科处方', '事前审查记录']},
            {'risk': 'medium', 'text': '医保乙类·国谈，每次注射后监测眼压（1日、1周、1月）', 'materials': ['眼压监测记录']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['眼科专科处方']},
        ],
        'other': ['玻璃体内植入操作须严格无菌', '注射后监测眼压', '告知患者白内障进展风险'],
    },

    '环孢素滴眼液(Ⅱ)': {
        'en_name': 'Cyclosporine Eye Drops (II)', 'category': '钙调磷酸酶抑制剂·眼科', 'is_essential': False,
        'indications': [
            {'text': '用于干眼症伴角结膜干燥症、干燥综合征相关干眼的抗炎治疗。', 'icd10': 'H04.100', 'offlabel': False},
        ],
        'dosage': ['每次1滴，每日2次（间隔12h）', '长期使用（起效需4-6周）'],
        'adverse_reactions': ['眼部烧灼感/刺痛（最常见，发生率17%）', '视物模糊（一过性）'],
        'contraindications': ['活动性眼部感染', '对环孢素过敏者'],
        'interactions': ['与其他眼药水间隔≥15分钟使用'],
        'special_populations': ['妊娠期：慎用', '儿童：安全性和有效性未确定'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有干眼症明确诊断（OSDI评分≥13或Schirmer试验<10mm/5min或角膜荧光染色阳性）', 'materials': ['干眼症诊断记录（OSDI/Schirmer/角膜染色）']},
            {'risk': 'medium', 'text': '医保乙类·国谈', 'materials': ['眼科专科处方']},
            {'risk': 'low', 'text': '医保乙类·国谈', 'materials': ['处方']},
        ],
        'other': ['起效缓慢（4-6周）', '需长期使用', '使用前摇匀'],
    },
"""

with open(r'D:\AI_libra\codex_Obsi\_builder\drug\build_drug_info.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert before 普拉洛芬
content = content.replace("\n    '普拉洛芬': {", entries + "\n    '普拉洛芬': {")

with open(r'D:\AI_libra\codex_Obsi\_builder\drug\build_drug_info.py', 'w', encoding='utf-8') as f:
    f.write(content)

count = entries.count("'en_name'")
print(f"Inserted {count} drug entries")
