#!/usr/bin/env python3
"""Export SQLite to JSON for web app - split into main + detail"""
import sqlite3, json, os, re, gzip

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
DIR = os.path.join(os.path.dirname(__file__), "web")

def pad_icd9(code):
    code = str(code).strip()
    m = re.match(r'^(\d+)\.(\S+)', code)
    if m: return m.group(1).zfill(2) + '.' + m.group(2)
    return code

def compress(path):
    """gzip a file in-place (alongside original)"""
    gz_path = path + ".gz"
    with open(path, 'rb') as f_in, gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
        f_out.writelines(f_in)
    return gz_path

def export():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ═══ MAIN data.json (lightweight, for search) ═══
    main = {}

    # ICD-10 codes (compact)
    icd10 = []
    cur.execute("SELECT ic.code, ic.name, ch.chapter_no, ch.name as chapter_name FROM icd10_codes ic JOIN icd10_sections s ON ic.section_id=s.id JOIN icd10_chapters ch ON s.chapter_id=ch.id ORDER BY ic.code")
    for row in cur.fetchall():
        icd10.append({"c": row["code"], "n": row["name"], "ch": row["chapter_no"], "chn": row["chapter_name"]})
    main["icd10"] = icd10

    # ICD-10 clinical mapping (compact: yb→clin lookup only)
    clin = {}
    cur.execute("SELECT clin_code, clin_name, yb_code, yb_name, is_same FROM icd10_clinical_map")
    for row in cur.fetchall():
        clin.setdefault(row["yb_code"], []).append({"cl": row["clin_code"], "cn": row["clin_name"], "s": row["is_same"]})
    # Fuzzy x-suffix match
    cur.execute("SELECT code FROM icd10_codes")
    grey10 = 0
    for (code,) in cur.fetchall():
        if code not in clin:
            m = re.match(r'^([A-Z]\d{2}\.\d+)x\d+$', code)
            if m and m.group(1) in clin: clin[code] = clin[m.group(1)]
            else:
                found = False
                for k in clin:
                    if k.startswith(code) and len(k) > len(code):
                        clin[code] = clin[k]; found = True; break
                if not found: clin[code] = []; grey10 += 1
    main["clin"] = clin
    print(f"ICD-10: {len(icd10)} codes, {grey10} grey")

    # ICD-9 codes
    icd9 = []
    cur.execute("SELECT i9.code, i9.name, ch9.name as chapter_name FROM icd9_codes i9 JOIN icd9_chapters ch9 ON i9.chapter_id=ch9.id ORDER BY i9.code")
    for row in cur.fetchall():
        icd9.append({"c": row["code"], "n": row["name"], "chn": row["chapter_name"]})
    main["icd9"] = icd9

    # ICD-9 clinical mapping
    clin9 = {}
    cur.execute("SELECT clin_code, clin_name, yb_code, yb_name, is_same, exclude_drg, category, entry_option FROM icd9_clinical_map")
    for row in cur.fetchall():
        info = {"cl": row["clin_code"], "cn": row["clin_name"], "s": row["is_same"],
                "drg": row["exclude_drg"], "cat": row["category"], "e": row["entry_option"]}
        yb = pad_icd9(row["yb_code"])
        clin9.setdefault(yb, []).append(info)
        stripped = re.sub(r'^0+(\d)', r'\1', yb)
        if stripped != yb: clin9.setdefault(stripped, []).append(info)
        m = re.match(r'^(\d+\.\d+?)0{2,}$', yb)
        if m:
            short, ss = m.group(1), re.sub(r'^0+(\d)', r'\1', m.group(1))
            for k in [short, ss]:
                if k != yb and k != stripped and k not in clin9: clin9[k] = [info]

    grey9 = 0
    cur.execute("SELECT DISTINCT code FROM icd9_codes")
    for row in cur.fetchall():
        code = pad_icd9(str(row["code"]).strip())
        if code not in clin9: clin9[code] = []; grey9 += 1
    main["clin9"] = clin9
    print(f"ICD-9: {len(icd9)} codes, {grey9} grey")

    # DIP 2.0 核心病种
    dips = []
    cur.execute("SELECT dip_code, dx_code, dx_name, px_code, px_name, rel_px_code, rel_px_name FROM dip_groups ORDER BY CAST(SUBSTR(dip_code,4) AS INTEGER)")
    for row in cur.fetchall():
        dips.append({
            "c": row["dip_code"],
            "dx": row["dx_code"],
            "dxn": row["dx_name"],
            "px": row["px_code"] or "",
            "pxn": row["px_name"] or "",
            "rpx": row["rel_px_code"] or "",
            "rpxn": row["rel_px_name"] or ""
        })
    main["dip"] = dips

    # Multitrauma zones
    mt = {}
    cur.execute("SELECT icd10_code, zone FROM multitrauma_zones")
    for row in cur.fetchall():
        mt[row[0]] = row[1]
    main["mt_zone"] = mt

    path = os.path.join(DIR, "data.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(main, f, ensure_ascii=False)
    gz = compress(path)
    sz, gz_sz = os.path.getsize(path), os.path.getsize(gz)
    print(f"data.json: {sz/1024/1024:.1f} MB → {gz_sz/1024:.1f} KB gzip")

    # ═══ DETAIL detail.json (hierarchy + lead terms, lazy load) ═══
    detail = {}

    # ICD-10 hierarchy
    h10 = {}
    cur.execute("SELECT code, cat_code, cat_name, sub_code, sub_name, sec_range, sec_name, ch_range, ch_name, ch_no FROM icd10_hierarchy")
    for row in cur.fetchall():
        h10[row["code"]] = {"ca": row["cat_code"], "can": row["cat_name"], "su": row["sub_code"],
            "sun": row["sub_name"], "se": row["sec_range"], "sen": row["sec_name"],
            "ch": row["ch_range"], "chn": row["ch_name"], "cno": row["ch_no"]}
    detail["h10"] = h10

    # ICD-9 hierarchy
    h9 = {}
    cur.execute("SELECT code, det_code, det_name, sub_code, sub_name, cat_code, cat_name, ch_no, ch_name FROM icd9_hierarchy")
    for row in cur.fetchall():
        info = {"det": row["det_code"], "det_n": row["det_name"], "sub": row["sub_code"],
                "sub_n": row["sub_name"], "cat": row["cat_code"], "cat_n": row["cat_name"],
                "ch_no": row["ch_no"], "ch_n": row["ch_name"]}
        code = str(row["code"]).strip()
        h9[code] = info
        m = re.match(r'^(\d+)\.(\d+)$', code)
        if m:
            padded = m.group(1).zfill(2) + '.' + m.group(2).ljust(4, '0')
            if padded != code: h9[padded] = info
    detail["h9"] = h9

    # ICD-9 lead terms
    lead = {}
    cur.execute("SELECT code, full_path, lead_term FROM icd9_lead_terms")
    for row in cur.fetchall():
        code = str(row["code"]).strip()
        m = re.match(r'^(\d+\.\d{2})', code)
        key = m.group(1) if m else code
        lead.setdefault(key, []).append({"p": row["full_path"], "t": row["lead_term"]})
    detail["lead"] = lead

    path2 = os.path.join(DIR, "detail.json")
    with open(path2, "w", encoding="utf-8") as f:
        json.dump(detail, f, ensure_ascii=False)
    gz2 = compress(path2)
    sz2, gz2_sz = os.path.getsize(path2), os.path.getsize(gz2)
    print(f"detail.json: {sz2/1024/1024:.1f} MB → {gz2_sz/1024:.1f} KB gzip")

    # ═══ DRG lookup data (separate file, for simulator) ═══
    # MDC names (standard DRG 2.0 mapping)
    mdc_names = {
        'MDCA':'先期分组','MDCB':'神经系统疾病及功能障碍','MDCC':'眼疾病及功能障碍',
        'MDCD':'耳鼻咽喉疾病及功能障碍','MDCE':'呼吸系统疾病及功能障碍',
        'MDCF':'循环系统疾病及功能障碍','MDCG':'消化系统疾病及功能障碍',
        'MDCH':'肝、胆、胰疾病及功能障碍','MDCI':'肌肉骨骼疾病及功能障碍',
        'MDCJ':'皮肤、皮下组织及乳腺疾病','MDCK':'内分泌、营养、代谢疾病',
        'MDCL':'肾脏及泌尿道疾病','MDCM':'男性生殖系统疾病',
        'MDCN':'女性生殖系统疾病','MDCO':'妊娠、分娩及产褥期',
        'MDCP':'新生儿及其他围产期疾病','MDCQ':'血液、免疫疾病',
        'MDCR':'骨髓增生疾病及功能障碍','MDCS':'感染及寄生虫病',
        'MDCT':'精神疾病','MDCU':'酒精/药物使用障碍','MDCV':'创伤、中毒',
        'MDCW':'烧伤','MDCX':'影响健康因素','MDCY':'HIV感染','MDCZ':'多发性创伤'
    }
    # ADRG prefix -> MDC mapping
    prefix_mdc = {}
    for code in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        prefix_mdc[code] = 'MDC'+code

    cur.execute("SELECT id, adrg_code, name, category, conditions, remark FROM drg_adrg")
    adrg_info = {}
    adrg_mdc = {}
    for row in cur.fetchall():
        code = row[1]; name = row[2]
        adrg_info[row[0]] = {"c": code, "n": name, "cat": row[3] or '', "cond": row[4] or '', "rem": row[5] or ''}
        p = code[0] if code else 'X'
        mdc = prefix_mdc.get(p, 'MDCZ')
        adrg_mdc[code] = {"mdc": mdc, "mdc_n": mdc_names.get(mdc, ''), "cat": row[3] or '', "cond": row[4] or '', "rem": row[5] or ''}

    cur.execute("SELECT adrg_id, drg_code, name, severity FROM drg_groups")
    drg_info = {}
    for row in cur.fetchall():
        drg_info.setdefault(row[0], []).append({"c": row[1], "n": row[2], "s": row[3]})

    # dx → adrg
    dx2a = {}
    cur.execute("SELECT icd10_code, adrg_id FROM adrg_diagnosis_map")
    for row in cur.fetchall():
        if row[0] and row[0] != 'nan':
            adrg = adrg_info.get(row[1])
            if adrg: dx2a.setdefault(row[0], []).append({"a": adrg["c"], "an": adrg["n"], "d": drg_info.get(row[1], [])})

    # px → adrg
    px2a = {}
    cur.execute("SELECT icd9_code, adrg_id FROM adrg_procedure_map")
    for row in cur.fetchall():
        if row[0] and row[0] != 'nan':
            adrg = adrg_info.get(row[1])
            if adrg: px2a.setdefault(row[0], []).append({"a": adrg["c"], "an": adrg["n"], "d": drg_info.get(row[1], [])})

    # MCC/CC lists with exclusion table reference
    mcc_set = set()
    mcc_tbl = {}  # code → which exclusion table it belongs to
    cur.execute("SELECT icd10_code, excluded FROM mcc_list")
    for c, tbl in cur.fetchall():
        mcc_set.add(c)
        if tbl and tbl.strip(): mcc_tbl[c] = tbl.strip()

    # MCC hierarchy lookup: sub_code + sub_name
    # When sub_code is empty (category-level codes), fall back to cat_code
    mcc_hier = {}
    cur.execute("SELECT code, sub_code, sub_name, cat_code, cat_name FROM icd10_hierarchy")
    hier_map = {}
    for code, sub_code, sub_name, cat_code, cat_name in cur.fetchall():
        if sub_code:
            hier_map[code] = [sub_code, sub_name]
        elif cat_code:
            hier_map[code] = [cat_code, cat_name]
    for code in mcc_set:
        if code in hier_map:
            mcc_hier[code] = hier_map[code]
        else:
            xcode = code + 'x001'
            if xcode in hier_map:
                mcc_hier[code] = hier_map[xcode]
    print(f"MCC hierarchy: {len(mcc_hier)}/{len(mcc_set)} codes mapped")

    cc_set = set()
    cc_tbl = {}
    cur.execute("SELECT icd10_code, excluded FROM cc_list")
    for c, tbl in cur.fetchall():
        cc_set.add(c)
        if tbl and tbl.strip(): cc_tbl[c] = tbl.strip()

    # Exclusions: which diagnoses are excluded from being CC/MCC
    # Keyed by table_name; value = set of excluded ICD-10 codes
    excl_map = {}
    cur.execute("SELECT table_name, icd10_code FROM cc_exclusions")
    for row in cur.fetchall():
        excl_map.setdefault(row[0], set()).add(row[1])

    # Non-grouping lists
    ng_dx = set()
    for (c,) in cur.execute("SELECT icd10_code FROM no_group_dx").fetchall(): ng_dx.add(c)
    ng_px = set()
    for (c,) in cur.execute("SELECT icd9_code FROM no_group_px").fetchall(): ng_px.add(c)

    drg_data = {
        "adrg": {k: {"c": v["c"], "n": v["n"]} for k, v in adrg_info.items()},
        "adrg_mdc": adrg_mdc,
        "dx2a": dx2a,
        "px2a": px2a,
        "mcc": list(mcc_set),
        "mcc_tbl": mcc_tbl,
        "cc": list(cc_set),
        "cc_tbl": cc_tbl,
        "excl": {k: list(v) for k, v in excl_map.items()},
        "no_dx": list(ng_dx),
        "no_px": list(ng_px),
        "mt_zone": mt,
        "mcc_hier": mcc_hier
    }
    path3 = os.path.join(DIR, "drg.json")
    with open(path3, "w", encoding="utf-8") as f:
        json.dump(drg_data, f, ensure_ascii=False)
    gz3 = compress(path3)
    print(f"drg.json: {os.path.getsize(path3)/1024/1024:.1f} MB → {os.path.getsize(gz3)/1024:.1f} KB gzip")

    conn.close()

if __name__ == "__main__":
    export()
