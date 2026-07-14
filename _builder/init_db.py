#!/usr/bin/env python3
"""
ICD 编码知识库 · 数据库初始化
创建 SQLite 数据库并写入种子数据（ICD-10 / ICD-9 / DRG / DIP / 案例）
运行：python init_db.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")

def init_db():
    # 如果已存在则删除重建
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # 加载 Schema
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # ═══════════════════════════════════════
    # ICD-10 章节
    # ═══════════════════════════════════════
    icd10_chapters = [
        (1, "A00-B99", "某些传染病和寄生虫病", "01-某些传染病和寄生虫病(A00-B99)"),
        (2, "C00-D48", "肿瘤", "02-肿瘤(C00-D48)"),
        (3, "D50-D89", "血液及造血器官疾病和涉及免疫机制的某些疾患", "03-血液及造血器官疾病和涉及免疫机制的某些疾患(D50-D89)"),
        (4, "E00-E90", "内分泌、营养和代谢疾病", "04-内分泌、营养和代谢疾病(E00-E90)"),
        (5, "F00-F99", "精神和行为障碍", "05-精神和行为障碍(F00-F99)"),
        (6, "G00-G99", "神经系统疾病", "06-神经系统疾病(G00-G99)"),
        (7, "H00-H59", "眼和附器疾病", "07-眼和附器疾病(H00-H59)"),
        (8, "H60-H95", "耳和乳突疾病", "08-耳和乳突疾病(H60-H95)"),
        (9, "I00-I99", "循环系统疾病", "09-循环系统疾病(I00-I99)"),
        (10, "J00-J99", "呼吸系统疾病", "10-呼吸系统疾病(J00-J99)"),
        (11, "K00-K93", "消化系统疾病", "11-消化系统疾病(K00-K93)"),
        (12, "L00-L99", "皮肤和皮下组织疾病", "12-皮肤和皮下组织疾病(L00-L99)"),
        (13, "M00-M99", "肌肉骨骼系统和结缔组织疾病", "13-肌肉骨骼系统和结缔组织疾病(M00-M99)"),
        (14, "N00-N99", "泌尿生殖系统疾病", "14-泌尿生殖系统疾病(N00-N99)"),
        (15, "O00-O99", "妊娠、分娩和产褥期", "15-妊娠、分娩和产褥期(O00-O99)"),
        (16, "P00-P96", "起源于围生期的某些情况", "16-起源于围生期的某些情况(P00-P96)"),
        (17, "Q00-Q99", "先天性畸形、变形和染色体异常", "17-先天性畸形、变形和染色体异常(Q00-Q99)"),
        (18, "R00-R99", "症状、体征和异常临床发现", "18-症状、体征和临床与实验室异常所见，不可归类在他处者(R00-R99)"),
        (19, "S00-T98", "损伤、中毒和外因的某些其他后果", "19-损伤、中毒和外因的某些其他后果(S00-T98)"),
        (20, "V01-Y98", "疾病和死亡的外因", "20-疾病和死亡的外因(V01-Y98)"),
        (21, "Z00-Z99", "影响健康状态和与保健机构接触的因素", "21-影响健康状态和与保健机构接触的因素(Z00-Z99)"),
        (22, "U00-U85", "特殊目的编码", "22-用于特殊目的的编码(U00-U85)"),
    ]
    cursor.executemany(
        "INSERT INTO icd10_chapters (chapter_no, code_range, name, folder_name) VALUES (?,?,?,?)",
        icd10_chapters
    )

    # ═══════════════════════════════════════
    # ICD-10 第一章：传染病 节 + 编码
    # ═══════════════════════════════════════
    ch1_sections = [
        (1, "A00-A09", "肠道传染病", "霍乱、伤寒、副伤寒、沙门菌、志贺菌、其他细菌性肠道感染、阿米巴病等", "非感染性腹泻(K52.9)"),
        (1, "A15-A19", "结核病", "肺结核、肺外结核、粟粒性结核", "结核病后遗症(B90)"),
        (1, "A20-A28", "某些动物源性细菌病", "鼠疫、土拉菌病、炭疽、布鲁菌病、钩端螺旋体病等", None),
        (1, "A30-A49", "其他细菌性疾病", "麻风、白喉、百日咳、猩红热、脑膜炎球菌感染等", None),
        (1, "A50-A64", "主要为性传播模式的感染", "梅毒、淋病、衣原体性病、软下疳等", None),
        (1, "B15-B19", "病毒性肝炎", "急性甲肝、急性乙肝、慢性乙肝、其他病毒性肝炎", "肝炎后遗症"),
        (1, "B20-B24", "人类免疫缺陷病毒病(HIV)", "HIV 伴各种感染和肿瘤", None),
    ]
    cursor.executemany(
        "INSERT INTO icd10_sections (chapter_id, code_range, name, includes, excludes) VALUES (?,?,?,?,?)",
        ch1_sections
    )

    ch1_codes = [
        (1, "A00.0", "古典生物型霍乱"),
        (1, "A00.1", "埃尔托生物型霍乱"),
        (1, "A01.0", "伤寒"),
        (1, "A02.0", "沙门菌肠炎"),
        (1, "A03.0", "痢疾志贺菌痢疾"),
        (1, "A03.9", "细菌性痢疾，未特指"),
        (1, "A04.7", "艰难梭菌性小肠结肠炎"),
        (1, "A08.0", "轮状病毒性肠炎"),
        (1, "A08.1", "诺如病毒性急性胃肠病"),
        (1, "A09.0", "感染性胃肠炎"),
        (2, "A15.0", "肺结核，痰镜检阳性"),
        (2, "A15.9", "肺结核，未特指"),
        (2, "A16.2", "肺结核，未提及细菌学或组织学证实"),
        (6, "B15.9", "急性甲型肝炎"),
        (6, "B16.9", "急性乙型肝炎"),
        (6, "B18.1", "慢性乙型肝炎"),
        (6, "B18.2", "慢性丙型肝炎"),
        (7, "B20.0", "HIV 病伴有分枝杆菌感染"),
        (7, "B24", "HIV 病，未特指"),
    ]
    cursor.executemany(
        "INSERT INTO icd10_codes (section_id, code, name) VALUES (?,?,?)",
        ch1_codes
    )

    # ═══════════════════════════════════════
    # ICD-10 第二章：肿瘤 节 + 编码
    # ═══════════════════════════════════════
    ch2_sections = [
        (2, "C00-C14", "唇、口腔和咽恶性肿瘤"),
        (2, "C15-C26", "消化器官恶性肿瘤"),
        (2, "C30-C39", "呼吸和胸腔内器官恶性肿瘤"),
        (2, "C43-C44", "皮肤黑色素瘤和其他皮肤恶性肿瘤"),
        (2, "C50", "乳腺恶性肿瘤"),
        (2, "C51-C58", "女性生殖器官恶性肿瘤"),
        (2, "C60-C63", "男性生殖器官恶性肿瘤"),
        (2, "C64-C68", "泌尿道恶性肿瘤"),
        (2, "C69-C72", "眼、脑和中枢神经系统恶性肿瘤"),
        (2, "C73-C75", "甲状腺和其他内分泌腺恶性肿瘤"),
        (2, "C76-C80", "不明确、继发和未特指部位恶性肿瘤"),
        (2, "C81-C96", "淋巴、造血和相关组织恶性肿瘤"),
        (2, "D00-D09", "原位癌"),
        (2, "D10-D36", "良性肿瘤"),
        (2, "D37-D48", "动态未定或动态未知的肿瘤"),
    ]
    cursor.executemany(
        "INSERT INTO icd10_sections (chapter_id, code_range, name) VALUES (?,?,?)",
        ch2_sections
    )

    ch2_codes = [
        (9, "C15.9", "食管恶性肿瘤，未特指"),
        (9, "C16.9", "胃恶性肿瘤，未特指"),
        (9, "C18.9", "结肠恶性肿瘤，未特指"),
        (9, "C20", "直肠恶性肿瘤"),
        (9, "C22.0", "肝细胞癌"),
        (9, "C25.9", "胰腺恶性肿瘤，未特指"),
        (10, "C34.9", "支气管或肺恶性肿瘤，未特指"),
        (11, "C43.9", "皮肤恶性黑色素瘤，未特指"),
        (12, "C50.9", "乳腺恶性肿瘤，未特指"),
        (19, "C81.9", "霍奇金淋巴瘤，未特指"),
        (19, "C85.9", "非霍奇金淋巴瘤，未特指"),
        (19, "C91.00", "急性淋巴细胞白血病，未缓解"),
        (19, "C92.00", "急性髓系白血病，未缓解"),
        (22, "D12.6", "结肠良性肿瘤"),
    ]
    cursor.executemany(
        "INSERT INTO icd10_codes (section_id, code, name) VALUES (?,?,?)",
        ch2_codes
    )

    # ═══════════════════════════════════════
    # ICD-10 第九章：循环系统（DRG 用的最多）
    # ═══════════════════════════════════════
    ch9_sections = [
        (9, "I00-I02", "急性风湿热"),
        (9, "I05-I09", "慢性风湿性心脏病"),
        (9, "I10-I15", "高血压病"),
        (9, "I20-I25", "缺血性心脏病"),
        (9, "I26-I28", "肺原性心脏病和肺循环疾病"),
        (9, "I30-I52", "其他类型心脏病"),
        (9, "I60-I69", "脑血管疾病"),
        (9, "I70-I79", "动脉、小动脉和毛细血管疾病"),
        (9, "I80-I89", "静脉和淋巴管疾病"),
    ]
    cursor.executemany(
        "INSERT INTO icd10_sections (chapter_id, code_range, name) VALUES (?,?,?)",
        ch9_sections
    )

    # 这些 ID 需要计算：前面插入了 ch1(7节) + ch2(15节) + 当前
    # ch9 sections 从第 7+15+1 = 23 开始
    ch9_id_start = 23
    ch9_codes = [
        (ch9_id_start+2, "I10", "原发性高血压"),
        (ch9_id_start+2, "I11.0", "高血压心脏病伴心力衰竭"),
        (ch9_id_start+2, "I11.9", "高血压心脏病不伴心力衰竭"),
        (ch9_id_start+2, "I12.0", "高血压肾脏病伴肾衰竭"),
        (ch9_id_start+2, "I13.0", "高血压心脏病和肾脏病伴心力衰竭"),
        (ch9_id_start+3, "I20.0", "不稳定型心绞痛"),
        (ch9_id_start+3, "I20.8", "其他类型心绞痛"),
        (ch9_id_start+3, "I20.9", "心绞痛，未特指"),
        (ch9_id_start+3, "I21.0", "急性前壁心肌梗死"),
        (ch9_id_start+3, "I21.3", "急性下壁心肌梗死"),
        (ch9_id_start+3, "I21.4", "急性心内膜下心肌梗死"),
        (ch9_id_start+3, "I21.9", "急性心肌梗死，未特指"),
        (ch9_id_start+3, "I22.9", "再发性心肌梗死，未特指"),
        (ch9_id_start+3, "I25.1", "冠状动脉粥样硬化性心脏病"),
        (ch9_id_start+3, "I25.2", "陈旧性心肌梗死"),
        (ch9_id_start+4, "I26.9", "肺栓塞，未提及急性肺源性心脏病"),
        (ch9_id_start+5, "I48", "心房颤动"),
        (ch9_id_start+5, "I48.0", "阵发性心房颤动"),
        (ch9_id_start+5, "I48.1", "持续性心房颤动"),
        (ch9_id_start+5, "I49.5", "病态窦房结综合征"),
        (ch9_id_start+5, "I50.0", "充血性心力衰竭"),
        (ch9_id_start+5, "I50.9", "心力衰竭，未特指"),
        (ch9_id_start+6, "I63.0", "脑梗死，由于脑前动脉血栓形成"),
        (ch9_id_start+6, "I63.5", "脑梗死，由于脑动脉闭塞或狭窄"),
        (ch9_id_start+6, "I63.9", "脑梗死，未特指"),
        (ch9_id_start+6, "I61.9", "脑出血，未特指"),
        (ch9_id_start+6, "I65.2", "颈动脉闭塞和狭窄"),
        (ch9_id_start+7, "I70.2", "四肢动脉粥样硬化"),
        (ch9_id_start+8, "I84.9", "痔，未特指"),
    ]
    cursor.executemany(
        "INSERT INTO icd10_codes (section_id, code, name) VALUES (?,?,?)",
        ch9_codes
    )

    # ═══════════════════════════════════════
    # ICD-9 手术操作 章节
    # ═══════════════════════════════════════
    icd9_chapters = [
        (1, "0.01-00.8700x001", "操作和介入不能分类于他处", "01-操作和介入不能分类于他处(0.01-00.8700x001)"),
        (2, "01.0100x002-5.89", "神经系统手术", "02-神经系统手术(01.0100x002-5.89)"),
        (3, "06.0100x001-7.9901", "内分泌系统手术", "03-内分泌系统手术(06.0100x001-7.9901)"),
        (4, "08.2000x003-9.99", "眼部手术", "04-眼部手术(08.2000x003-9.99)"),
        (5, "1.79E+01-17.9994", "其他各类诊断性和治疗性操作", "05-其他各类诊断性和治疗性操作(1.79E+01-17.9994)"),
        (6, "18.01-20.9903", "耳部手术", "06-耳部手术(18.01-20.9903)"),
        (7, "21-29.99", "鼻、口、咽部手术", "07-鼻、口、咽部手术(21-29.99)"),
        (8, "30.01-34.9905", "呼吸系统手术", "08-呼吸系统手术(30.01-34.9905)"),
        (9, "35-39.99", "心血管系统手术", "09-心血管系统手术(35-39.99)"),
        (10, "40.0x00-41.9901", "造血和淋巴系统手术", "10-造血和淋巴系统手术(40.0x00-41.9901)"),
        (11, "42.01-54.9904", "消化系统手术", "11-消化系统手术(42.01-54.9904)"),
        (12, "55.01-59.9903", "泌尿系统手术", "12-泌尿系统手术(55.01-59.9903)"),
        (13, "60.0x00-64.99", "男性生殖系统手术", "13-男性生殖系统手术(60.0x00-64.99)"),
        (14, "65.01-71.9x00", "女性生殖系统手术", "14-女性生殖系统手术(65.01-71.9x00)"),
        (15, "72.0x00-75.9902", "产科操作", "15-产科操作(72.0x00-75.9902)"),
        (16, "76.01-84.99", "肌肉骨骼系统手术", "16-肌肉骨骼系统手术(76.01-84.99)"),
        (17, "85.0x00-86.99", "体被系统手术", "17-体被系统手术(85.0x00-86.99)"),
        (18, "39.9500x004-99.9902", "其他诊断性和治疗性操作", "18-其他诊断性和治疗性操作(39.9500x004-99.9902)"),
    ]
    cursor.executemany(
        "INSERT INTO icd9_chapters (chapter_no, code_range, name, folder_name) VALUES (?,?,?,?)",
        icd9_chapters
    )

    # ICD-9 高频手术编码
    icd9_codes = [
        # 消化系统 (ch8, id=8)
        (8, "42.41", "食管部分切除术"),
        (8, "43.7", "胃部分切除术"),
        (8, "43.89", "胃切除术，其他"),
        (8, "44.41", "胃溃疡缝合术"),
        (8, "45.73", "右半结肠切除术"),
        (8, "45.75", "左半结肠切除术"),
        (8, "45.76", "乙状结肠切除术"),
        (8, "47.01", "腹腔镜阑尾切除术"),
        (8, "47.09", "其他阑尾切除术"),
        (8, "51.22", "胆囊切除术"),
        (8, "51.23", "腹腔镜胆囊切除术"),
        (8, "54.11", "剖腹探查术"),
        (8, "54.21", "腹腔镜检查"),
        # 心血管 (ch6, id=6)
        (6, "35.21", "主动脉瓣置换术"),
        (6, "35.22", "二尖瓣置换术"),
        (6, "36.10", "主动脉冠状动脉搭桥术"),
        (6, "36.12", "二支冠状动脉搭桥术"),
        (6, "36.13", "三支冠状动脉搭桥术"),
        (6, "36.06", "冠状动脉支架置入术"),
        (6, "37.22", "左心导管检查"),
        (6, "38.93", "中心静脉置管"),
        (6, "39.95", "血液透析"),
        # 呼吸系统 (ch5, id=5)
        (5, "32.4", "肺叶切除术"),
        (5, "34.04", "胸腔闭式引流"),
        (5, "34.91", "胸腔穿刺术"),
        # 神经系统 (ch1, id=1)
        (1, "01.24", "开颅血肿清除术"),
        (1, "01.59", "脑病损切除术"),
        (1, "02.21", "脑室外引流术"),
        # 泌尿 (ch9, id=9)
        (9, "55.03", "经皮肾穿刺引流"),
        (9, "56.0", "经输尿管镜碎石取石术"),
        (9, "57.32", "膀胱镜检查"),
        (9, "60.29", "经尿道前列腺切除术(TURP)"),
        # 妇产科 (ch11, id=11)
        (11, "68.4", "经腹全子宫切除术"),
        (11, "68.51", "腹腔镜子宫切除术"),
        (11, "74.1", "低位子宫下段剖宫产"),
        # 骨科 (ch13, id=13)
        (13, "79.31", "肱骨骨折切开复位内固定"),
        (13, "79.35", "股骨骨折切开复位内固定"),
        (13, "80.51", "腰椎间盘切除术"),
        (13, "81.51", "全髋关节置换术"),
        (13, "81.54", "全膝关节置换术"),
        # 其他操作 (ch15, id=15)
        (15, "96.04", "气管插管"),
        (15, "96.71", "呼吸机治疗[连续]"),
        (15, "99.60", "心肺复苏"),
    ]
    cursor.executemany(
        "INSERT INTO icd9_codes (chapter_id, code, name) VALUES (?,?,?)",
        icd9_codes
    )

    # ═══════════════════════════════════════
    # DRG 2.0 分组数据（以循环系统为例）
    # ═══════════════════════════════════════

    # MDC
    mdcs = [
        ("MDCA", "神经系统疾病及功能障碍"),
        ("MDCB", "眼部疾病及功能障碍"),
        ("MDCC", "耳鼻咽喉疾病及功能障碍"),
        ("MDCD", "呼吸系统疾病及功能障碍"),
        ("MDCE", "循环系统疾病及功能障碍"),
        ("MDCF", "消化系统疾病及功能障碍"),
        ("MDCG", "肝胆胰疾病及功能障碍"),
        ("MDCH", "肌肉骨骼疾病及功能障碍"),
        ("MDCI", "皮肤皮下组织及乳腺疾病"),
        ("MDCJ", "内分泌营养代谢疾病"),
        ("MDCK", "肾脏及泌尿道疾病"),
        ("MDCL", "男性生殖系统疾病"),
        ("MDCM", "女性生殖系统疾病"),
        ("MDCN", "妊娠分娩产褥期"),
        ("MDCO", "新生儿及其他围产期疾病"),
        ("MDCP", "血液免疫疾病及功能障碍"),
        ("MDCQ", "骨髓增生性疾病及功能障碍"),
        ("MDCR", "感染及寄生虫病"),
        ("MDCS", "精神疾病及功能障碍"),
        ("MDCT", "酒精/药物使用及功能障碍"),
        ("MDCU", "创伤、中毒及药物毒性效应"),
        ("MDCV", "烧伤"),
        ("MDCW", "影响健康状态因素"),
        ("MDCX", "其他多种重要创伤"),
        ("MDCY", "HIV 感染"),
    ]
    cursor.executemany(
        "INSERT INTO drg_mdc (mdc_code, name) VALUES (?,?)",
        mdcs
    )

    # ADRG（以 MDCE 循环系统为例）
    adrg_surgical = [
        ("FB1", "主动脉手术", "surgical"),
        ("FB2", "冠状动脉搭桥术", "surgical"),
        ("FC1", "冠状动脉介入治疗(PCI)", "surgical"),
        ("FC2", "其他经皮心血管操作", "surgical"),
        ("FD1", "心脏起搏器植入术", "surgical"),
        ("FD2", "心脏除颤器植入术", "surgical"),
        ("FE1", "瓣膜手术", "surgical"),
        ("FF1", "其他开胸心脏手术", "surgical"),
        ("FG1", "大血管手术", "surgical"),
        ("FH1", "截肢（循环障碍）", "surgical"),
    ]
    adrg_medical = [
        ("FJ1", "急性心肌梗死", "medical"),
        ("FK1", "心力衰竭", "medical"),
        ("FL1", "心律失常", "medical"),
        ("FM1", "心绞痛/冠心病", "medical"),
        ("FN1", "高血压", "medical"),
        ("FP1", "脑血管疾病", "medical"),
        ("FQ1", "周围血管疾病", "medical"),
        ("FR1", "其他循环系统疾病", "medical"),
    ]

    adrg_id_map = {}
    for adrg_code, name, adrg_type in adrg_surgical + adrg_medical:
        cursor.execute(
            "INSERT INTO drg_adrg (mdc_id, adrg_code, name, type) VALUES (5,?,?,?)",
            (adrg_code, name, adrg_type)
        )
        adrg_id_map[adrg_code] = cursor.lastrowid

    # DRG 组（ADRG 下的细分）
    drg_groups = [
        # FB2 冠状动脉搭桥术
        ("FB2", "FB21", "冠状动脉搭桥术，伴MCC", "MCC", 4.50, 180000, 25),
        ("FB2", "FB23", "冠状动脉搭桥术，伴CC", "CC", 3.80, 150000, 20),
        ("FB2", "FB25", "冠状动脉搭桥术，不伴MCC/CC", "noCC", 3.20, 130000, 17),
        # FC1 PCI
        ("FC1", "FC11", "PCI，伴MCC", "MCC", 1.80, 60000, 10),
        ("FC1", "FC13", "PCI，伴CC", "CC", 1.30, 45000, 7),
        ("FC1", "FC15", "PCI，不伴MCC/CC", "noCC", 0.90, 30000, 5),
        # FJ1 急性心肌梗死
        ("FJ1", "FJ11", "急性心肌梗死，伴MCC", "MCC", 1.60, 35000, 12),
        ("FJ1", "FJ13", "急性心肌梗死，伴CC", "CC", 1.10, 25000, 9),
        ("FJ1", "FJ15", "急性心肌梗死，不伴MCC/CC", "noCC", 0.80, 18000, 7),
        # FK1 心力衰竭
        ("FK1", "FK11", "心力衰竭，伴MCC", "MCC", 1.50, 32000, 11),
        ("FK1", "FK13", "心力衰竭，伴CC", "CC", 1.00, 22000, 8),
        ("FK1", "FK15", "心力衰竭，不伴MCC/CC", "noCC", 0.70, 15000, 6),
        # FL1 心律失常
        ("FL1", "FL11", "心律失常，伴MCC", "MCC", 1.40, 28000, 9),
        ("FL1", "FL13", "心律失常，伴CC", "CC", 0.90, 18000, 6),
        ("FL1", "FL15", "心律失常，不伴MCC/CC", "noCC", 0.60, 12000, 4),
        # FM1 心绞痛/冠心病
        ("FM1", "FM11", "心绞痛/冠心病，伴MCC", "MCC", 1.20, 22000, 9),
        ("FM1", "FM13", "心绞痛/冠心病，伴CC", "CC", 0.80, 15000, 6),
        ("FM1", "FM15", "心绞痛/冠心病，不伴MCC/CC", "noCC", 0.55, 10000, 4),
        # FN1 高血压
        ("FN1", "FN11", "高血压，伴MCC", "MCC", 1.00, 18000, 8),
        ("FN1", "FN13", "高血压，伴CC", "CC", 0.70, 12000, 5),
        ("FN1", "FN15", "高血压，不伴MCC/CC", "noCC", 0.45, 8000, 3),
        # FP1 脑血管疾病
        ("FP1", "FP11", "脑血管疾病，伴MCC", "MCC", 2.00, 45000, 15),
        ("FP1", "FP13", "脑血管疾病，伴CC", "CC", 1.20, 30000, 11),
        ("FP1", "FP15", "脑血管疾病，不伴MCC/CC", "noCC", 0.80, 18000, 7),
    ]

    for adrg_code, drg_code, name, severity, weight, cost, days in drg_groups:
        cursor.execute(
            "INSERT INTO drg_groups (adrg_id, drg_code, name, severity, weight, avg_cost, avg_days) VALUES (?,?,?,?,?,?,?)",
            (adrg_id_map[adrg_code], drg_code, name, severity, weight, cost, days)
        )

    # ═══════════════════════════════════════
    # DRG 诊断映射（主要诊断决定 ADRG）
    # ═══════════════════════════════════════
    # 获取编码 ID
    cursor.execute("SELECT id, code FROM icd10_codes")
    icd10_ids = {row[1]: row[0] for row in cursor.fetchall()}
    cursor.execute("SELECT id, code FROM icd9_codes")
    icd9_ids = {row[1]: row[0] for row in cursor.fetchall()}
    cursor.execute("SELECT id, drg_code FROM drg_groups")
    drg_ids = {row[1]: row[0] for row in cursor.fetchall()}

    # 诊断→DRG 映射（主要诊断）
    dx_drg_maps = [
        # 急性心肌梗死 → FJ1 系列
        ("I21.0", "FJ15"), ("I21.3", "FJ15"), ("I21.4", "FJ15"), ("I21.9", "FJ15"),
        # 再发性心梗 → FJ1
        ("I22.9", "FJ15"),
        # 心力衰竭 → FK1 系列
        ("I50.0", "FK15"), ("I50.9", "FK15"),
        # 心律失常 → FL1 系列
        ("I48", "FL15"), ("I48.0", "FL15"), ("I48.1", "FL15"), ("I49.5", "FL15"),
        # 心绞痛 → FM1 系列
        ("I20.0", "FM15"), ("I20.8", "FM15"), ("I20.9", "FM15"),
        # 冠心病 → FM1
        ("I25.1", "FM15"), ("I25.2", "FM15"),
        # 高血压 → FN1 系列
        ("I10", "FN15"), ("I11.0", "FN15"), ("I11.9", "FN15"),
        # 脑血管 → FP1 系列
        ("I63.9", "FP15"), ("I63.0", "FP15"), ("I61.9", "FP15"), ("I65.2", "FP15"),
    ]

    for icd10_code, drg_code in dx_drg_maps:
        if icd10_code in icd10_ids and drg_code in drg_ids:
            cursor.execute(
                "INSERT INTO drg_diagnosis_map (drg_id, icd10_id, is_primary) VALUES (?,?,1)",
                (drg_ids[drg_code], icd10_ids[icd10_code])
            )

    # 手术→DRG 映射
    proc_drg_maps = [
        # 搭桥→FB2
        ("36.10", "FB25"), ("36.12", "FB25"), ("36.13", "FB25"),
        # 支架→FC1
        ("36.06", "FC15"),
        # 瓣膜→FE1（暂无数据）
        # TURP→泌尿相关（暂不映射）
    ]
    for icd9_code, drg_code in proc_drg_maps:
        if icd9_code in icd9_ids and drg_code in drg_ids:
            cursor.execute(
                "INSERT INTO drg_procedure_map (drg_id, icd9_id, is_primary) VALUES (?,?,1)",
                (drg_ids[drg_code], icd9_ids[icd9_code])
            )

    # ═══════════════════════════════════════
    # DIP 3.0 病种分组（示例）
    # ═══════════════════════════════════════
    dip_samples = [
        ("DIP-E01", "急性心肌梗死-无手术", "I21.9", None, 22000, 1.2),
        ("DIP-E02", "急性心肌梗死-PCI治疗", "I21.9", "36.06", 45000, 1.8),
        ("DIP-E03", "心力衰竭", "I50.9", None, 18000, 0.8),
        ("DIP-E04", "心房颤动", "I48", None, 12000, 0.6),
        ("DIP-E05", "冠心病-药物治疗", "I25.1", None, 13000, 0.7),
        ("DIP-E06", "脑梗死-无手术", "I63.9", None, 25000, 1.3),
        ("DIP-E07", "高血压-药物治疗", "I10", None, 8000, 0.45),
        ("DIP-F01", "阑尾炎-腹腔镜手术", "K35.8", "47.01", 15000, 0.8),
        ("DIP-F02", "胆囊结石-腹腔镜手术", "K80.2", "51.23", 18000, 1.0),
        ("DIP-G01", "充血性心力衰竭", "I50.0", None, 20000, 1.1),
        ("DIP-G02", "肺栓塞", "I26.9", None, 28000, 1.5),
    ]

    for code, name, icd10_code, icd9_code, cost, weight in dip_samples:
        icd10_id = icd10_ids.get(icd10_code)
        icd9_id = icd9_ids.get(icd9_code) if icd9_code else None
        cursor.execute(
            "INSERT INTO dip_groups (dip_code, name, icd10_primary_id, icd9_primary_id, avg_cost, weight) VALUES (?,?,?,?,?,?)",
            (code, name, icd10_id, icd9_id, cost, weight)
        )

    # ═══════════════════════════════════════
    # 案例数据（真实病例样式）
    # ═══════════════════════════════════════
    cases = [
        ("C2024-0001", "M", 68, "2024-01-05", "2024-01-17", "心内科",
         48230.50, "FJ15", "DIP-E01",
         "因胸痛3小时入院。急诊心电图示前壁ST段抬高。冠脉造影示LAD近端95%狭窄，行PCI+支架植入术。术后恢复良好。"),
        ("C2024-0002", "F", 72, "2024-01-08", "2024-01-22", "心内科",
         35600.00, "FK15", "DIP-E03",
         "因呼吸困难、下肢水肿入院。既往高血压、糖尿病史。心脏彩超示EF35%。诊断急性心力衰竭，予利尿、扩血管等治疗。"),
        ("C2024-0003", "M", 55, "2024-01-12", "2024-01-15", "心内科",
         18000.00, "FL15", "DIP-E04",
         "突发心悸入院，ECG示房颤。给予胺碘酮转律，成功恢复窦性心律。"),
        ("C2024-0004", "M", 78, "2024-02-02", "2024-02-28", "心外科",
         185000.00, "FB25", None,
         "冠脉CTA示三支病变，择期行不停跳三支冠状动脉搭桥术。术中平稳，术后ICU观察后转入普通病房。"),
        ("C2024-0005", "F", 64, "2024-02-10", "2024-02-20", "神经内科",
         32000.00, "FP15", "DIP-E06",
         "突发言语不清、右侧肢体无力2小时入院。CT示左侧基底节区脑梗死。给予溶栓+抗血小板治疗。"),
        ("C2024-0006", "M", 35, "2024-03-01", "2024-03-08", "普外科",
         16500.00, None, "DIP-F01",
         "右下腹痛1天入院。体检麦氏点压痛反跳痛。B超示阑尾炎。急诊腹腔镜阑尾切除术，术后抗感染。"),
        ("C2024-0007", "F", 45, "2024-03-05", "2024-03-12", "肝胆外科",
         19500.00, None, "DIP-F02",
         "反复右上腹痛。B超示胆囊结石。择期腹腔镜胆囊切除术，术中发现慢性胆囊炎表现。"),
        ("C2024-0008", "M", 82, "2024-03-20", "2024-04-15", "心内科",
         62000.00, "FJ11", "DIP-E01",
         "急性广泛前壁心肌梗死伴心源性休克入院。IABP支持下急诊PCI，术后并发急性肾损伤，CRRT治疗。"),
    ]

    cursor.executemany(
        "INSERT INTO cases (case_no, gender, age, admission, discharge, dept, total_cost, drg_result, dip_result, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        cases
    )

    # 案例诊断（手动指定，实际场景需要准确链接）
    # 简化为每个案例手动绑定诊断编码
    case_dx = {
        1: [("I21.0", 1), ("I25.1", 2), ("I10", 3), ("E11.9", 4)],  # AMI + HTN + DM
        2: [("I50.0", 1), ("I11.0", 2), ("I48", 3)],                 # CHF + HTN heart + AF
        3: [("I48.0", 1), ("I10", 2)],                                # AF + HTN
        4: [("I25.1", 1), ("I21.9", 2), ("I10", 3)],                  # CAD + old MI + HTN
        5: [("I63.5", 1), ("I10", 2), ("I65.2", 3)],                  # cerebral infarction
        6: [("K35.8", 1)],                                             # appendicitis
        7: [("K80.2", 1)],                                             # cholecystolithiasis
        8: [("I21.0", 1), ("I50.0", 2), ("I10", 3), ("N17.9", 4)],   # AMI + shock + AKI
    }

    for case_id, diags in case_dx.items():
        for icd10_code, rank in diags:
            if icd10_code in icd10_ids:
                cursor.execute(
                    "INSERT INTO case_diagnoses (case_id, icd10_id, rank) VALUES (?,?,?)",
                    (case_id, icd10_ids[icd10_code], rank)
                )

    # 案例手术
    case_proc = {
        1: [("36.06", 1)],    # PCI+stent
        4: [("36.13", 1)],    # CABG x3
        6: [("47.01", 1)],    # lap appendectomy
        7: [("51.23", 1)],    # lap cholecystectomy
    }

    for case_id, procs in case_proc.items():
        for icd9_code, rank in procs:
            if icd9_code in icd9_ids:
                cursor.execute(
                    "INSERT INTO case_procedures (case_id, icd9_id, rank) VALUES (?,?,?)",
                    (case_id, icd9_ids[icd9_code], rank)
                )

    conn.commit()

    # ═══════════════════════════════════════
    # 统计摘要
    # ═══════════════════════════════════════
    stats = {
        "icd10_chapters": cursor.execute("SELECT COUNT(*) FROM icd10_chapters").fetchone()[0],
        "icd10_sections": cursor.execute("SELECT COUNT(*) FROM icd10_sections").fetchone()[0],
        "icd10_codes": cursor.execute("SELECT COUNT(*) FROM icd10_codes").fetchone()[0],
        "icd9_chapters": cursor.execute("SELECT COUNT(*) FROM icd9_chapters").fetchone()[0],
        "icd9_codes": cursor.execute("SELECT COUNT(*) FROM icd9_codes").fetchone()[0],
        "drg_mdc": cursor.execute("SELECT COUNT(*) FROM drg_mdc").fetchone()[0],
        "drg_adrg": cursor.execute("SELECT COUNT(*) FROM drg_adrg").fetchone()[0],
        "drg_groups": cursor.execute("SELECT COUNT(*) FROM drg_groups").fetchone()[0],
        "dip_groups": cursor.execute("SELECT COUNT(*) FROM dip_groups").fetchone()[0],
        "cases": cursor.execute("SELECT COUNT(*) FROM cases").fetchone()[0],
        "case_diagnoses": cursor.execute("SELECT COUNT(*) FROM case_diagnoses").fetchone()[0],
        "case_procedures": cursor.execute("SELECT COUNT(*) FROM case_procedures").fetchone()[0],
    }

    conn.close()

    import sys
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

    print("[OK] Database initialized!")
    print(f"File: {DB_PATH}")
    print(f"Stats:")
    for k, v in stats.items():
        print(f"   {k}: {v}")
    print(
        f"\nTotal records: {sum(stats.values())}\n"
        f"Next: python generate_md.py  -> Obsidian notes\n"
        f"      python generate_web.py -> Web data"
    )

if __name__ == "__main__":
    init_db()
