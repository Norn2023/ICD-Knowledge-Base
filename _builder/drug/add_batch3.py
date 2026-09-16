"""Add batch 3: top 20 处方集 drugs by variant count"""
entries = """
    '维生素C': {
        'en_name': 'Vitamin C (Ascorbic Acid)', 'category': '维生素类', 'is_essential': False,
        'indications': [
            {'text': '用于维生素C缺乏症（坏血病）的预防和治疗。', 'icd10': 'E54.x00', 'offlabel': False},
            {'text': '用于急慢性感染、创伤愈合期、贫血等的辅助治疗。', 'icd10': 'Z51.800', 'offlabel': False},
        ],
        'dosage': ['口服：100-300mg/日，分次服用', '静脉：0.5-1g/日'],
        'adverse_reactions': ['大剂量可致腹泻、泌尿系结石'],
        'contraindications': ['高草酸盐尿症', 'G6PD缺乏者大剂量使用可致溶血'],
        'interactions': ['巴比妥类：增加维生素C代谢', '铁剂：增加铁吸收'],
        'special_populations': ['妊娠期：安全（不超过推荐量）', '肾功能不全：慎用大剂量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确维生素C缺乏症诊断或特定疾病辅助治疗指征；单纯"增强免疫力"使用医保拒付', 'materials': ['符合适应症的病历记录']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['常规剂量安全性好', '大剂量可致胃肠不适'],
    },

    '阿司匹林': {
        'en_name': 'Aspirin', 'category': 'NSAID/抗血小板药', 'is_essential': True,
        'indications': [
            {'text': '用于不稳定性心绞痛、急性心肌梗死、PCI术后等动脉粥样硬化性心血管疾病的抗血小板治疗。', 'icd10': 'I25.101', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
            {'text': '用于缺血性脑卒中/TIA的抗血小板治疗和二级预防。', 'icd10': 'I63.900', 'offlabel': False},
            {'text': '用于解热镇痛（头痛、牙痛、肌肉痛、痛经、发热等）。', 'icd10': 'R52.900', 'offlabel': False},
        ],
        'dosage': ['抗血小板：75-100mg qd', '解热镇痛：300-600mg q4-6h'],
        'adverse_reactions': ['消化道溃疡/出血（抗血小板剂量即可发生）', '出血时间延长', '过敏反应', '阿司匹林哮喘'],
        'contraindications': ['活动性消化性溃疡', '出血性疾病', '严重肝肾功能不全', '妊娠晚期', '阿司匹林哮喘史'],
        'interactions': ['其他NSAID/抗凝药/抗血小板药：增加出血风险', '甲氨蝶呤：增加毒性', 'ACEI：降低降压效果'],
        'special_populations': ['妊娠期：孕晚期禁用', '儿童病毒感染：避免使用（Reye综合征风险）'],
        'insurance_notes': [
            {'risk': 'high', 'text': '活动性消化性溃疡或出血性疾病者禁用', 'materials': ['消化道出血风险评估']},
            {'risk': 'medium', 'text': '医保甲类·基药，冠心病(I25)和脑梗死(I63)属门诊慢病', 'materials': ['确诊病历', '门诊处方']},
            {'risk': 'low', 'text': '医保甲类·基药', 'materials': ['门诊处方']},
        ],
        'other': ['肠溶片须整片吞服', '抗血小板剂量75-100mg/日安全窗', '术前需停药5-7天'],
    },

    '阿奇霉素': {
        'en_name': 'Azithromycin', 'category': '大环内酯类抗生素', 'is_essential': False,
        'indications': [
            {'text': '用于呼吸道感染（社区获得性肺炎、急性咽炎/扁桃体炎、急性支气管炎等）。', 'icd10': 'J15.900', 'offlabel': False},
            {'text': '用于非淋菌性尿道炎/宫颈炎（沙眼衣原体）。', 'icd10': 'A56.000', 'offlabel': False},
        ],
        'dosage': ['成人：500mg qd×3天', '儿童：10mg/kg qd×3天'],
        'adverse_reactions': ['胃肠道反应（恶心、腹泻）', 'QTc间期延长（罕见，心血管风险患者慎用）', '肝酶升高'],
        'contraindications': ['对大环内酯类过敏者', 'QTc间期延长者或联用延长QTc药物者慎用'],
        'interactions': ['延长QTc的药物（胺碘酮、氟喹诺酮类等）', '华法林：可能增强抗凝', '他汀类：增加肌病风险'],
        'special_populations': ['妊娠期：可用', '哺乳期：可用', '肝功能不全：慎用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确感染诊断方可支付，非感染性使用医保拒付', 'materials': ['感染诊断编码', 'CRP/PCT']},
            {'risk': 'medium', 'text': '医保乙类，QTc延长风险患者须评估', 'materials': ['心电图（QTc）']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['半衰期长（68h），3天疗程可维持7天疗效', '空腹服用吸收最佳'],
    },

    '辛伐他汀': {
        'en_name': 'Simvastatin', 'category': '他汀类降脂药', 'is_essential': True,
        'indications': [
            {'text': '用于原发性高胆固醇血症和混合型高脂血症的降脂治疗。', 'icd10': 'E78.000', 'offlabel': False},
            {'text': '用于冠心病合并高胆固醇血症，降低心血管事件风险。', 'icd10': 'I25.101', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
        ],
        'dosage': ['起始10-20mg qn', '最大40mg qn（中国人群避免80mg）', '晚间服用效果最佳'],
        'adverse_reactions': ['肌痛/肌炎（横纹肌溶解罕见但严重）', '肝酶升高', '与CYP3A4抑制剂联用增加肌病风险'],
        'contraindications': ['活动性肝病', '妊娠及哺乳期', '与吉非罗齐、CYP3A4强抑制剂联用'],
        'interactions': ['CYP3A4抑制剂（克拉霉素、伊曲康唑、利托那韦等）→ 禁用或减量', '吉非罗齐：显著增加横纹肌溶解→禁用', '华法林：增强抗凝'],
        'special_populations': ['妊娠期：禁用', '中国人：80mg/日不推荐（肌病风险高）'],
        'insurance_notes': [
            {'risk': 'high', 'text': '与吉非罗齐或CYP3A4强抑制剂（克拉霉素等）联用属绝对禁忌', 'materials': ['合并用药审查']},
            {'risk': 'medium', 'text': '医保甲类·基药，冠心病属门诊慢病', 'materials': ['血脂报告', '肝功能+肌酸激酶监测']},
            {'risk': 'low', 'text': '医保甲类·基药', 'materials': ['门诊处方']},
        ],
        'other': ['晚间服用', '中国人群限制40mg/日', '监测肝功能+肌酸激酶'],
    },

    '替米沙坦': {
        'en_name': 'Telmisartan', 'category': 'ARB类降压药', 'is_essential': False,
        'indications': [
            {'text': '用于原发性高血压的治疗。', 'icd10': 'I10.x00', '慢病': True, '慢病名称': '高血压', 'offlabel': False},
            {'text': '用于降低心血管疾病高危患者的心血管事件风险。', 'icd10': 'I25.101', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
        ],
        'dosage': ['40-80mg qd', '最大80mg/日'],
        'adverse_reactions': ['头晕', '高钾血症', '肾功能损害（肾动脉狭窄者风险高）'],
        'contraindications': ['双侧肾动脉狭窄', '妊娠中晚期', '严重肝功能不全', '与阿利吉仑联用（糖尿病患者）'],
        'interactions': ['保钾利尿剂/补钾：增加高钾血症风险', '锂盐：增加锂毒性', 'NSAID：降低降压效果+增加肾损害'],
        'special_populations': ['妊娠期：禁用（中晚期）', '肾功能不全：CCr<30起始减量', '肝功能不全：Child-Pugh C级减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '双侧肾动脉狭窄患者禁用；妊娠期禁用', 'materials': ['肾动脉超声（如可疑）', '妊娠状态确认']},
            {'risk': 'medium', 'text': '医保乙类，高血压(I10)属门诊慢病', 'materials': ['血压监测记录', '肾功能+血钾报告']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['半衰期24h（长效ARB）', '有PPARγ激动作用（轻度改善胰岛素抵抗）'],
    },

    '庆大霉素': {
        'en_name': 'Gentamicin', 'category': '氨基糖苷类抗生素', 'is_essential': False,
        'indications': [
            {'text': '用于铜绿假单胞菌等敏感革兰阴性菌所致的重症感染。', 'icd10': 'B96.500', 'offlabel': False},
        ],
        'dosage': ['IV：3-6mg/kg/日 分3次', 'TDM：谷浓度<2mg/L，峰浓度5-10mg/L'],
        'adverse_reactions': ['肾毒性（10-20%）', '耳毒性（不可逆）', '神经肌肉阻滞'],
        'contraindications': ['重症肌无力', '对氨基糖苷类过敏'],
        'interactions': ['其他肾毒性药物（万古霉素、两性霉素B、顺铂）→增加毒性'],
        'special_populations': ['妊娠期：慎用（可致胎儿耳毒性）', '肾功能不全：必须TDM减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有药敏证据+血药浓度TDM监测', 'materials': ['药敏报告', 'TDM监测记录']},
            {'risk': 'medium', 'text': '医保甲类，疗程<10天，每日监测肾功能', 'materials': ['肾功能监测记录']},
            {'risk': 'low', 'text': '医保甲类', 'materials': ['处方']},
        ],
        'other': ['必须TDM监测', '充足水化', '每日监测肾功能'],
    },

    '利伐沙班': {
        'en_name': 'Rivaroxaban', 'category': '直接Xa因子抑制剂·口服抗凝', 'is_essential': False,
        'indications': [
            {'text': '用于非瓣膜性房颤（NVAF）的卒中预防。', 'icd10': 'I48.x00', '慢病': True, '慢病名称': '心房颤动', 'offlabel': False},
            {'text': '用于深静脉血栓（DVT）和肺栓塞（PE）的治疗和二级预防。', 'icd10': 'I26.900', 'offlabel': False},
            {'text': '用于髋/膝关节置换术后VTE预防。', 'icd10': 'Z51.800', 'offlabel': False},
        ],
        'dosage': ['NVAF卒中预防：20mg qd（CCr 15-49→15mg qd）', 'DVT/PE治疗：15mg bid×3周→20mg qd', 'VTE预防：10mg qd'],
        'adverse_reactions': ['出血（颅内、消化道等，发生率约3-5%/年）', '肝酶升高'],
        'contraindications': ['活动性出血', '严重肝病伴凝血障碍', '妊娠及哺乳期', 'CCr<15（NVAF）'],
        'interactions': ['抗血小板药/NSAID：增加出血风险', 'CYP3A4+P-gp强抑制剂（酮康唑、利托那韦）：禁用', 'CYP3A4+P-gp强诱导剂（利福平）：避免合用'],
        'special_populations': ['妊娠期：禁用', '肾功能不全：CCr 15-49减量至15mg qd', 'CCr<15：不推荐'],
        'insurance_notes': [
            {'risk': 'high', 'text': 'CCr<15禁用（NVAF）；活动性出血禁用', 'materials': ['eGFR检测报告', '出血风险评估']},
            {'risk': 'medium', 'text': '医保乙类，房颤卒中预防须CHA₂DS₂-VASc≥2分(男)/≥3分(女)', 'materials': ['房颤诊断记录', '卒中风险评分记录']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['专科处方']},
        ],
        'other': ['固定剂量，无需常规凝血监测', '与餐同服（15mg/20mg）', '不可掰开或压碎'],
    },

    '非布司他': {
        'en_name': 'Febuxostat', 'category': '黄嘌呤氧化酶抑制剂·降尿酸', 'is_essential': False,
        'indications': [
            {'text': '用于痛风患者高尿酸血症的长期降尿酸治疗（别嘌醇不耐受或禁忌时）。', 'icd10': 'M10.900', 'offlabel': False},
        ],
        'dosage': ['起始40mg qd，2周后血尿酸未达标→80mg qd'],
        'adverse_reactions': ['痛风急性发作（降尿酸初期，需同时使用秋水仙碱/NSAID预防3-6月）', '肝酶升高', '心血管事件风险（FDA黑框警告：心血管死亡风险高于别嘌醇）'],
        'contraindications': ['正在使用硫唑嘌呤/6-巯基嘌呤的患者'],
        'interactions': ['硫唑嘌呤/6-MP：非布司他抑制黄嘌呤氧化酶→显著增加其毒性→禁用'],
        'special_populations': ['妊娠期：不推荐', '肝功能不全：监测肝酶', '心血管疾病史：慎用（考虑改用别嘌醇）'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有别嘌醇不耐受或禁忌的病历记录方可支付；心血管疾病史者慎用（FDA黑框警告）', 'materials': ['别嘌醇使用史及不耐受/禁忌记录', '心血管病史评估']},
            {'risk': 'medium', 'text': '医保乙类，降尿酸初期须同时使用秋水仙碱/NSAID预防痛风发作3-6月', 'materials': ['联合预防用药处方', '血尿酸监测记录']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['风湿科/内分泌科处方']},
        ],
        'other': ['心血管高风险者优选别嘌醇', '降尿酸初期预防痛风发作', '监测肝功能'],
    },

    '罗红霉素': {
        'en_name': 'Roxithromycin', 'category': '大环内酯类抗生素', 'is_essential': False,
        'indications': [
            {'text': '用于敏感菌所致的呼吸道感染、泌尿生殖道感染、皮肤软组织感染等。', 'icd10': 'J15.900', 'offlabel': False},
        ],
        'dosage': ['成人：150mg bid 餐前服用'],
        'adverse_reactions': ['胃肠道反应', '肝酶升高', 'QTc延长（少见）'],
        'contraindications': ['对大环内酯类过敏'],
        'interactions': ['麦角胺：增加麦角中毒风险', '延长QTc药物'],
        'special_populations': ['妊娠期：慎用', '肝功能不全：减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确感染诊断', 'materials': ['感染诊断编码']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['餐前服用吸收佳', '胃肠道耐受性优于红霉素'],
    },

    '硝苯地平': {
        'en_name': 'Nifedipine', 'category': 'CCB类降压药', 'is_essential': True,
        'indications': [
            {'text': '用于原发性高血压的治疗。', 'icd10': 'I10.x00', '慢病': True, '慢病名称': '高血压', 'offlabel': False},
            {'text': '用于变异型心绞痛和慢性稳定性心绞痛。', 'icd10': 'I20.801', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
        ],
        'dosage': ['控释片：30-60mg qd', '缓释片：10-20mg bid', '注意：短效速释剂不推荐长期降压'],
        'adverse_reactions': ['头痛、面部潮红（血管扩张）', '踝部水肿', '心悸/心动过速（短效剂型明显）', '牙龈增生（长期使用）'],
        'contraindications': ['心源性休克', '严重主动脉瓣狭窄', '不稳定心绞痛（短效剂型）'],
        'interactions': ['CYP3A4抑制剂（克拉霉素等）：升高硝苯地平血药浓度→减量', '西柚汁：增加硝苯地平生物利用度'],
        'special_populations': ['妊娠期：可用（妊娠期高血压一线用药）', '肝功能不全：减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '短效速释硝苯地平不推荐长期降压（血压波动大、反射性心率增快）', 'materials': ['处方须为控释或缓释剂型']},
            {'risk': 'medium', 'text': '医保甲类·基药，高血压(I10)和冠心病(I20)属门诊慢病', 'materials': ['血压监测记录']},
            {'risk': 'low', 'text': '医保甲类·基药', 'materials': ['门诊处方']},
        ],
        'other': ['控释片不可掰开', '避免与西柚汁同服', '牙龈增生需注意口腔卫生'],
    },

    '利巴韦林': {
        'en_name': 'Ribavirin', 'category': '广谱抗病毒药', 'is_essential': False,
        'indications': [
            {'text': '用于呼吸道合胞病毒（RSV）所致的严重下呼吸道感染（吸入剂）。', 'icd10': 'J12.100', 'offlabel': False},
            {'text': '联合干扰素用于慢性丙型肝炎的治疗。', 'icd10': 'B18.200', 'offlabel': False},
        ],
        'dosage': ['口服：800-1200mg/日 分2次', 'HCV治疗：按体重和基因型调整'],
        'adverse_reactions': ['溶血性贫血（剂量依赖性，发生率10-15%）', '致畸性（孕妇及配偶禁用，停药后仍需避孕6月）'],
        'contraindications': ['妊娠及可能妊娠', '哺乳期', '严重心脏病', '血红蛋白病'],
        'interactions': ['齐多夫定：增加贫血风险'],
        'special_populations': ['妊娠期：绝对禁用', '男性：停药后避孕≥7月'],
        'insurance_notes': [
            {'risk': 'high', 'text': '孕妇及配偶绝对禁用（致畸）；溶血性贫血须定期监测血红蛋白', 'materials': ['妊娠状态确认', '血红蛋白监测']},
            {'risk': 'medium', 'text': '医保乙类', 'materials': ['感染科处方']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['处方']},
        ],
        'other': ['孕妇及配偶绝对禁用', '停药后避孕≥6-7月', '监测血红蛋白'],
    },

    '格列齐特': {
        'en_name': 'Gliclazide', 'category': '磺脲类口服降糖药', 'is_essential': False,
        'indications': [
            {'text': '用于成人2型糖尿病的血糖控制（饮食和运动控制不佳，且不适合使用二甲双胍时）。', 'icd10': 'E11.900', '慢病': True, '慢病名称': '糖尿病', 'offlabel': False},
        ],
        'dosage': ['起始40-80mg/日', '最大320mg/日', '餐前30分钟服用'],
        'adverse_reactions': ['低血糖（最重要，长效磺脲低血糖可持续数天）', '体重增加', '胃肠道反应'],
        'contraindications': ['1型糖尿病', 'DKA', '严重肝肾功能不全', '妊娠及哺乳期', '磺胺类过敏'],
        'interactions': ['酒精：双硫仑样反应（格列齐特含磺脲结构）+低血糖', 'NSAID/华法林/磺胺类：增强降糖效应', '糖皮质激素/利尿剂：升高血糖'],
        'special_populations': ['妊娠期：禁用', '老年人：从低剂量起始（低血糖风险高）', '肾功能不全：CCr<30禁用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '低血糖风险（长效磺脲，可持续数天），老年人及肾功能不全者慎用；CCr<30禁用', 'materials': ['eGFR检测', '低血糖风险评估']},
            {'risk': 'medium', 'text': '医保乙类，2型糖尿病(E11)属门诊慢病', 'materials': ['血糖监测记录', 'HbA1c报告']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['餐前30分钟服用', '低血糖风险（长效）', '磺胺过敏者禁用'],
    },

    '替格瑞洛': {
        'en_name': 'Ticagrelor', 'category': 'P2Y12受体拮抗剂·抗血小板', 'is_essential': False,
        'indications': [
            {'text': '联合阿司匹林用于急性冠脉综合征（ACS）的双联抗血小板治疗（DAPT），预防血栓事件。', 'icd10': 'I25.101', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
        ],
        'dosage': ['负荷180mg→维持90mg bid，联合阿司匹林75-100mg qd', 'DAPT一般持续12个月'],
        'adverse_reactions': ['出血（所有抗血小板药共有风险）', '呼吸困难（替格瑞洛特征性不良反应，发生率13-15%，多为轻中度）', '高尿酸血症', '室性停搏（罕见）'],
        'contraindications': ['活动性出血', '颅内出血史', '严重肝功能不全'],
        'interactions': ['CYP3A4强抑制剂（酮康唑等）：禁用', 'CYP3A4强诱导剂（利福平）：避免', '阿司匹林>100mg/日：降低替格瑞洛疗效'],
        'special_populations': ['妊娠期：慎用', '肝功能不全：严重者禁用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有ACS明确诊断方可支付；与阿司匹林联用须注意DAPT疗程（一般12月）', 'materials': ['ACS诊断记录', 'DAPT疗程记录']},
            {'risk': 'medium', 'text': '医保乙类，须告知患者呼吸困难可能（不影响肺功能，不需停药）', 'materials': ['患者告知记录']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['心内科处方']},
        ],
        'other': ['bid给药（与氯吡格雷qd不同）', '呼吸困难发生率13-15%（多可耐受）', '阿司匹林剂量≤100mg/日'],
    },

    '纳洛酮': {
        'en_name': 'Naloxone', 'category': '阿片受体拮抗剂', 'is_essential': False,
        'indications': [
            {'text': '用于阿片类药物过量的急救（逆转呼吸抑制）。', 'icd10': 'T40.200', 'offlabel': False},
            {'text': '用于术后阿片类药物过量效应（镇静、呼吸抑制）的逆转。', 'icd10': 'Z51.800', 'offlabel': False},
        ],
        'dosage': ['阿片过量：0.4-2mg IV/IM/SC q2-3min，最大10mg', '术后：0.1-0.2mg IV q2-3min至通气改善'],
        'adverse_reactions': ['急性戒断综合征（高血压、心动过速、肺水肿）', '恶心呕吐', '再镇静（纳洛酮半衰期短于多数阿片类药物）'],
        'contraindications': ['对纳洛酮过敏者', '阿片依赖者慎用（诱发戒断）'],
        'interactions': ['直接拮抗所有阿片类药物效应'],
        'special_populations': ['妊娠期：可用（紧急情况）', '新生儿：可用于阿片经胎盘暴露的呼吸抑制'],
        'insurance_notes': [
            {'risk': 'high', 'text': '限阿片类药物中毒或过量的急救使用', 'materials': ['阿片中毒/过量诊断记录']},
            {'risk': 'medium', 'text': '医保甲类，半衰期短需重复给药', 'materials': ['用药记录']},
            {'risk': 'low', 'text': '医保甲类', 'materials': ['处方']},
        ],
        'other': ['半衰期30-90分钟（短于多数阿片。需重复给药防再镇静）', '不可替代毒品戒断治疗'],
    },

    '氨甲环酸': {
        'en_name': 'Tranexamic Acid', 'category': '抗纤溶止血药', 'is_essential': False,
        'indications': [
            {'text': '用于纤溶亢进所致的出血（手术创伤、产后出血、月经过多等）。', 'icd10': 'D65.x00', 'offlabel': False},
        ],
        'dosage': ['IV：0.5-1g q8-12h', '口服：1-1.5g bid-tid'],
        'adverse_reactions': ['血栓形成风险（罕见过敏体质者）', '视觉障碍（色觉异常，罕见）', '低血压（快速静脉推注时）'],
        'contraindications': ['活动性血管内凝血', '蛛网膜下腔出血', '严重肾功能不全'],
        'interactions': ['激素类避孕药：增加血栓风险'],
        'special_populations': ['妊娠期：可用（产后出血一线）', '肾功能不全：按CCr减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '须有明确纤溶亢进或出血诊断方可支付；蛛网膜下腔出血禁用', 'materials': ['出血诊断记录', '纤溶亢进证据']},
            {'risk': 'medium', 'text': '医保乙类，产后出血为一线止血药', 'materials': ['产科记录']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['处方']},
        ],
        'other': ['产后出血一线止血药', '肾功能不全减量', '快速IV可致低血压'],
    },

    '阿卡波糖': {
        'en_name': 'Acarbose', 'category': 'α-糖苷酶抑制剂·口服降糖药', 'is_essential': False,
        'indications': [
            {'text': '用于2型糖尿病的血糖控制（主要降低餐后血糖），可单用或联合其他降糖药。', 'icd10': 'E11.900', '慢病': True, '慢病名称': '糖尿病', 'offlabel': False},
        ],
        'dosage': ['起始50mg tid，餐中第一口饭嚼服', '可增至100mg tid'],
        'adverse_reactions': ['胃肠胀气（碳水化合物在结肠发酵产气，发生率50-70%，随用药时间可减轻）', '腹泻、腹痛', '低血糖（单药不引起；联用其他降糖药时发生低血糖必须用葡萄糖纠正，不能用蔗糖）'],
        'contraindications': ['IBD、肠梗阻、消化吸收障碍', '严重肾功能不全（CCr<25）', '肝硬化'],
        'interactions': ['消化酶制剂（淀粉酶、胰酶）：降低阿卡波糖疗效', '考来烯胺：降低疗效'],
        'special_populations': ['妊娠期：不推荐', '肾功能不全：CCr<25禁用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '发生低血糖时须用葡萄糖纠正（不能用蔗糖/果汁——阿卡波糖抑制蔗糖分解）', 'materials': ['低血糖处理告知记录']},
            {'risk': 'medium', 'text': '医保甲类，2型糖尿病(E11)属门诊慢病', 'materials': ['血糖监测记录', 'HbA1c报告']},
            {'risk': 'low', 'text': '医保甲类', 'materials': ['门诊处方']},
        ],
        'other': ['与第一口饭嚼服', '主要降低餐后血糖', '低血糖须用葡萄糖纠正'],
    },

    '克拉霉素': {
        'en_name': 'Clarithromycin', 'category': '大环内酯类抗生素', 'is_essential': False,
        'indications': [
            {'text': '用于敏感菌所致的呼吸道感染（社区获得性肺炎、急性支气管炎等）。', 'icd10': 'J15.900', 'offlabel': False},
            {'text': '联合阿莫西林+PPI用于根除幽门螺杆菌（Hp）的三联疗法。', 'icd10': 'B98.000', 'offlabel': False},
        ],
        'dosage': ['一般感染：250-500mg bid', 'Hp根除：500mg bid×10-14天'],
        'adverse_reactions': ['胃肠道反应', '味觉异常（金属味，特征性）', 'QTc延长', '肝酶升高'],
        'contraindications': ['QTc延长或联用延长QTc药物者', '严重肝功能不全'],
        'interactions': ['CYP3A4强抑制剂：显著升高多种药物血药浓度（他汀类、麦角胺、咪达唑仑等）', '秋水仙碱：增加毒性（禁用联合）'],
        'special_populations': ['妊娠期：慎用', '肝功能不全：慎用'],
        'insurance_notes': [
            {'risk': 'high', 'text': '为CYP3A4强抑制剂，与他汀联用增加横纹肌溶解风险；与秋水仙碱联用属禁忌', 'materials': ['合并用药审查（重点排查他汀/秋水仙碱）']},
            {'risk': 'medium', 'text': '医保乙类，Hp根除须联合阿莫西林+PPI组成规范的10-14天方案', 'materials': ['Hp检测报告', '联合处方']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['CYP3A4强抑制剂——多药相互作用', 'Hp根除标准三联组分之一'],
    },

    '厄贝沙坦': {
        'en_name': 'Irbesartan', 'category': 'ARB类降压药', 'is_essential': False,
        'indications': [
            {'text': '用于原发性高血压的治疗。', 'icd10': 'I10.x00', '慢病': True, '慢病名称': '高血压', 'offlabel': False},
            {'text': '用于2型糖尿病肾病伴高血压的肾脏保护治疗。', 'icd10': 'E11.201', '慢病': True, '慢病名称': '糖尿病肾病', 'offlabel': False},
        ],
        'dosage': ['150mg qd，可增至300mg qd'],
        'adverse_reactions': ['头晕', '高钾血症', '肾功能损害（肾动脉狭窄者）'],
        'contraindications': ['双侧肾动脉狭窄', '妊娠中晚期'],
        'interactions': ['保钾利尿剂：高钾血症', '锂盐：增加锂毒性', 'NSAID：降低降压效果'],
        'special_populations': ['妊娠期：禁用（中晚期）', '肾功能不全：CCr<30初始减量'],
        'insurance_notes': [
            {'risk': 'high', 'text': '双侧肾动脉狭窄/妊娠中晚期禁用', 'materials': ['肾动脉筛查', '妊娠状态记录']},
            {'risk': 'medium', 'text': '医保乙类，高血压+糖尿病肾病属慢病', 'materials': ['肾功能+血钾报告']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['长效（半衰期11-15h）', '糖尿病肾病肾脏保护证据充分'],
    },

    '瑞舒伐他汀': {
        'en_name': 'Rosuvastatin', 'category': '他汀类降脂药', 'is_essential': False,
        'indications': [
            {'text': '用于原发性高胆固醇血症和混合型高脂血症。', 'icd10': 'E78.000', 'offlabel': False},
            {'text': '用于冠心病的一级和二级预防。', 'icd10': 'I25.101', '慢病': True, '慢病名称': '冠心病', 'offlabel': False},
        ],
        'dosage': ['起始5-10mg qd', '最大20mg qd（中国人群限制）'],
        'adverse_reactions': ['肌痛/肌病', '肝酶升高', '蛋白尿（一过性，肾小管重吸收影响）'],
        'contraindications': ['活动性肝病', '妊娠及哺乳期', '严重肾功能不全'],
        'interactions': ['吉非罗齐：禁用', '环孢素：升高瑞舒伐他汀血药浓度', '华法林：增强抗凝'],
        'special_populations': ['妊娠期：禁用', '中国人：限制20mg/日（肌病风险）'],
        'insurance_notes': [
            {'risk': 'high', 'text': '与吉非罗齐联用属禁忌；中国人群限制20mg/日', 'materials': ['合并用药审查', '肝功能+肌酸激酶']},
            {'risk': 'medium', 'text': '医保乙类，冠心病属门诊慢病', 'materials': ['血脂报告']},
            {'risk': 'low', 'text': '医保乙类', 'materials': ['门诊处方']},
        ],
        'other': ['水溶性他汀（CYP2C9代谢，药物相互作用少）', '中国人群最大20mg/日'],
    },
"""

with open(r'D:\AI_libra\codex_Obsi\_builder\drug\build_drug_info.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("\n    '普拉洛芬': {", entries + "\n    '普拉洛芬': {")

with open(r'D:\AI_libra\codex_Obsi\_builder\drug\build_drug_info.py', 'w', encoding='utf-8') as f:
    f.write(content)

count = entries.count("'en_name'")
print(f"Inserted {count} drugs")
