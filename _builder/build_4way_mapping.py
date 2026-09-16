"""
四方映射构建工具
旧上海价格 ↔ 新立项指南 ↔ 2023技术规范 ↔ ICD-9-CM3

Phase 1: 数据加载与清洗
Phase 2: 映射构建
Phase 3: 输出汇总表
"""

import openpyxl
import pandas as pd
import json
import re
from difflib import SequenceMatcher
from collections import defaultdict

# ============================================================
# PHASE 1: 数据加载
# ============================================================

def load_shanghai_prices(filepath):
    """加载并清洗上海市医疗服务价格（2024年）"""
    print("Loading Shanghai prices...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb['Sheet1']

    all_rows = []
    for row in ws.iter_rows(min_row=1, values_only=True):
        all_rows.append([str(c) if c is not None else '' for c in row])
    wb.close()

    # Parse hierarchy: parent items define name, children inherit
    items = []
    current_category = ''
    current_parent_name = ''
    current_parent_desc = ''
    current_parent_code = ''

    for row in all_rows[1:]:  # Skip header
        code = row[0].strip()
        name = row[1].strip()
        desc = row[4].strip()
        excluded = row[6].strip()
        unit = row[9].strip()
        price_col11 = row[11].strip()
        price_col12 = row[12].strip()
        price_col13 = row[13].strip()
        notes = row[14].strip()

        if not code:
            continue

        # Category headers (short codes like '1', '102', '12')
        if re.match(r'^\d{1,2}$', code) or re.match(r'^\d{1,3}$', code):
            current_category = name
            continue

        # Parent items: have both code and name+description
        if name and not re.match(r'^[a-z]$', code[-1] if len(code)>6 else ''):
            # Check if this is a parent (has description or is a 6+ digit code without letter suffix)
            is_parent = True
            if len(code) >= 6:
                # It has a description or seems to be a standalone item
                current_parent_name = name
                current_parent_desc = desc
                current_parent_code = code
                # If it has a price, it's a standalone item too
                if price_col11:
                    items.append({
                        'sh_code': code,
                        'sh_name': name,
                        'sh_full_name': name,
                        'sh_desc': desc,
                        'sh_excluded': excluded,
                        'sh_unit': unit,
                        'sh_price': price_col11,
                        'sh_price_2': price_col12,
                        'sh_price_3': price_col13,
                        'sh_notes': notes,
                        'sh_category': current_category,
                        'is_subitem': False,
                        'parent_code': ''
                    })
                else:
                    # Pure parent, save as header
                    items.append({
                        'sh_code': code,
                        'sh_name': name,
                        'sh_full_name': name,
                        'sh_desc': desc,
                        'sh_excluded': excluded,
                        'sh_unit': unit,
                        'sh_price': '',
                        'sh_price_2': '',
                        'sh_price_3': '',
                        'sh_notes': notes,
                        'sh_category': current_category,
                        'is_subitem': False,
                        'parent_code': ''
                    })
                continue

        # Sub-items: have letter suffix, inherit parent name
        if name and current_parent_name:
            full_name = f"{current_parent_name}（{name}）"
            items.append({
                'sh_code': code,
                'sh_name': name,
                'sh_full_name': full_name,
                'sh_desc': current_parent_desc if not desc else desc,
                'sh_excluded': excluded,
                'sh_unit': unit if unit else '',
                'sh_price': price_col11,
                'sh_price_2': price_col12,
                'sh_price_3': price_col13,
                'sh_notes': notes,
                'sh_category': current_category,
                'is_subitem': True,
                'parent_code': current_parent_code
            })
        elif code and not name:
            # Item with code but no name - subitem without explicit name
            if current_parent_name and price_col11:
                full_name = f"{current_parent_name}"
                items.append({
                    'sh_code': code,
                    'sh_name': '',
                    'sh_full_name': full_name,
                    'sh_desc': current_parent_desc,
                    'sh_excluded': excluded,
                    'sh_unit': unit if unit else '',
                    'sh_price': price_col11,
                    'sh_price_2': price_col12,
                    'sh_price_3': price_col13,
                    'sh_notes': notes,
                    'sh_category': current_category,
                    'is_subitem': True,
                    'parent_code': current_parent_code
                })

    print(f"  Parsed {len(items)} Shanghai price items")
    print(f"  With prices: {sum(1 for i in items if i['sh_price'])}")
    print(f"  Categories: {len(set(i['sh_category'] for i in items if i['sh_category']))}")
    return items


def load_pricing_guide(filepath):
    """加载国家医疗价格立项指南"""
    print("Loading pricing guide...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)

    items = []
    # Main catalog sheet
    ws = wb['医疗价格目录']
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        items.append({
            'pg_seq': str(row[0]).strip() if row[0] else '',
            'pg_category': str(row[1]).strip() if row[1] else '',
            'pg_subseq': str(row[2]).strip() if row[2] else '',
            'pg_name': str(row[3]).strip().replace('\n', '') if row[3] else '',
            'pg_output': str(row[4]).strip() if row[4] else '',
            'pg_cost_structure': str(row[5]).strip() if row[5] else '',
            'pg_surcharge': str(row[6]).strip() if row[6] else '',
            'pg_extension': str(row[7]).strip() if row[7] else '',
            'pg_unit': str(row[8]).strip() if row[8] else '',
            'pg_unit_note': str(row[9]).strip() if row[9] else '',
        })
    wb.close()
    print(f"  Loaded {len(items)} pricing guide items")
    return items


def load_tech_specs(filepath):
    """加载2023全国医疗服务项目技术规范 - 使用'详细'sheet(含ICD-9编码)"""
    print("Loading 2023 tech specs...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)

    # Use '详细' sheet which has all items + ICD-9 codes
    ws = wb['详细']

    # Headers: 项目编码(0), 项目名称(中文)(1), 项目名称(英文)(2), (3), 医保ICD编码(4), 医保ICD名称(5), 项目内涵(6)
    all_items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        code = str(row[0]).strip() if row[0] else ''
        name = str(row[1]).strip() if row[1] else ''

        # Skip section headers (codes like 'A', 'AA', 'H', 'HA', etc.)
        if not code or len(code) <= 3:
            continue
        # Skip category headers
        if not name or name.startswith('本章说明'):
            continue

        icd_code = str(row[4]).strip() if len(row) > 4 and row[4] else ''
        icd_name = str(row[5]).strip() if len(row) > 5 and row[5] else ''
        desc = str(row[6]).strip()[:200] if len(row) > 6 and row[6] else ''

        all_items.append({
            'ts_code': code,
            'ts_name': name.replace('\n', ''),
            'ts_desc': desc,
            'ts_icd_code': icd_code,
            'ts_icd_name': icd_name,
            'ts_chapter': '',
        })

    wb.close()
    print(f"  Loaded {len(all_items)} tech spec items")
    print(f"  With ICD-9 codes: {sum(1 for i in all_items if i['ts_icd_code'])}")
    return all_items


def load_icd9_codes(filepath_html, filepath_guolin, filepath_duizhao):
    """加载ICD-9-CM3编码"""
    print("Loading ICD-9 codes...")

    icd9_items = []

    # 1. Parse HTML-format insurance version
    try:
        tables = pd.read_html(filepath_html, encoding='utf-8')
        if tables:
            df = tables[0]
            # The structure is multi-level, let's extract actual codes
            # Look for rows where col 2 (项目编码) is numeric
            for _, row in df.iterrows():
                code = str(row.iloc[2]).strip() if len(row) > 2 else ''
                name = str(row.iloc[3]).strip() if len(row) > 3 else ''
                detail_code = str(row.iloc[6]).strip() if len(row) > 6 else ''
                detail_name = str(row.iloc[7]).strip() if len(row) > 7 else ''

                if detail_code and re.match(r'^\d', detail_code):
                    icd9_items.append({
                        'icd9_code_yb': detail_code,
                        'icd9_name_yb': detail_name,
                        'icd9_code_parent': code,
                        'icd9_name_parent': name,
                    })
    except Exception as e:
        print(f"  Warning: HTML parse issue: {e}")

    # 2. Load 国临3.0 version
    try:
        wb = openpyxl.load_workbook(filepath_guolin, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        guolin_codes = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            code = str(row[0]).strip() if row[0] else ''
            name = str(row[2]).strip() if len(row) > 2 and row[2] else ''
            if code and name:
                guolin_codes[code] = name
        wb.close()
        print(f"  Loaded {len(guolin_codes)} 国临3.0 ICD-9 codes")
    except Exception as e:
        print(f"  Warning: 国临3.0 load issue: {e}")
        guolin_codes = {}

    # 3. Load 对照表
    duizhao = []
    try:
        wb = openpyxl.load_workbook(filepath_duizhao, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            gl_code = str(row[0]).strip() if row[0] else ''
            gl_name = str(row[1]).strip() if row[1] else ''
            yb_code = str(row[2]).strip() if row[2] else ''
            yb_name = str(row[3]).strip() if row[3] else ''
            same = str(row[4]).strip() if row[4] else ''
            drg_flag = str(row[5]).strip() if row[5] else ''
            duizhao.append({
                'gl_code': gl_code,
                'gl_name': gl_name,
                'yb_code': yb_code,
                'yb_name': yb_name,
                'same': same,
                'drg_flag': drg_flag,
            })
        wb.close()
        print(f"  Loaded {len(duizhao)} 对照表 entries")
    except Exception as e:
        print(f"  Warning: 对照表 load issue: {e}")

    return {
        'icd9_yb_list': icd9_items,
        'guolin_codes': guolin_codes,
        'duizhao': duizhao
    }


# ============================================================
# PHASE 2: 匹配引擎
# ============================================================

def clean_name(name):
    """标准化名称用于匹配"""
    name = name.replace('\n', '').replace('\r', '').strip()
    name = re.sub(r'[（(].*?[）)]', '', name)  # Remove parenthetical
    name = re.sub(r'\s+', '', name)
    return name


def fuzzy_match(name1, name2, threshold=0.6):
    """模糊匹配两个名称"""
    n1 = clean_name(name1)
    n2 = clean_name(name2)

    # Exact match after cleaning
    if n1 == n2:
        return 1.0

    # If one contains the other
    if n1 in n2 or n2 in n1:
        return 0.9

    # Sequence similarity
    return SequenceMatcher(None, n1, n2).ratio()


def build_similarity_index(items_a, key_a, items_b, key_b, threshold=0.5):
    """为两组items建立相似度索引"""
    matches = []
    for i, a in enumerate(items_a):
        name_a = a[key_a]
        if not name_a:
            continue
        best_score = 0
        best_b = None
        for j, b in enumerate(items_b):
            name_b = b[key_b]
            if not name_b:
                continue
            score = fuzzy_match(name_a, name_b)
            if score > best_score:
                best_score = score
                best_b = j
        if best_score >= threshold:
            matches.append({
                'idx_a': i,
                'idx_b': best_b,
                'score': best_score,
                'name_a': name_a,
                'name_b': items_b[best_b][key_b],
            })
    return matches


# ============================================================
# PHASE 3: 主流程
# ============================================================

def main():
    base = 'D:/AI_libra/codex_Obsi/_builder'

    # Load all data
    sh_items = load_shanghai_prices(f'{base}/上海市医疗服务价格汇总表（2024年）.xlsx')
    pg_items = load_pricing_guide(f'{base}/国家医疗价格立项指南--汇总版.xlsx')
    ts_items = load_tech_specs(f'{base}/全国医疗服务项目技术规范--2023全.xlsx')
    icd9_data = load_icd9_codes(
        f'{base}/ICD-9-CM3医保2(2026年5月从医保局官网下载）.xlsx',
        f'{base}/手术操作分类代码国家临床版3.0（2022汇总版）.xlsx',
        f'{base}/ICD9国临版3.0对照医保版2.0_0125.xlsx'
    )

    # Build ICD-9 lookup
    guolin_codes = icd9_data['guolin_codes']
    duizhao = icd9_data['duizhao']

    # Build 医保ICD code -> 国临code mapping from 对照表
    yb_to_gl = {}
    for d in duizhao:
        yb_to_gl[d['yb_code']] = d['gl_code']

    # Build 国临code -> name
    gl_name_map = {d['gl_code']: d['gl_name'] for d in duizhao if d['gl_name']}
    gl_name_map.update(guolin_codes)

    # STATISTICS
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    print(f"  上海旧价格项目: {len(sh_items)}")
    print(f"  国家立项指南项目: {len(pg_items)}")
    print(f"  2023技术规范项目: {len(ts_items)}")
    print(f"  ICD-9国临3.0编码: {len(guolin_codes)}")
    print(f"  ICD-9对照表条目: {len(duizhao)}")

    # Count tech specs with ICD-9
    ts_with_icd = [t for t in ts_items if t['ts_icd_code']]
    print(f"  技术规范含ICD-9: {len(ts_with_icd)}")

    # ============================================================
    # MAPPING 1: 技术规范 → ICD-9 (直接关联)
    # ============================================================
    print("\n--- Mapping 1: 技术规范 → ICD-9 ---")
    ts_icd_matches = []
    for t in ts_with_icd:
        icd = t['ts_icd_code']
        gl_code = yb_to_gl.get(icd, icd)
        gl_full_name = gl_name_map.get(gl_code, '')
        yb_full_name = ''
        for d in duizhao:
            if d['yb_code'] == icd:
                yb_full_name = d['yb_name']
                break
        ts_icd_matches.append({
            'ts_code': t['ts_code'],
            'ts_name': t['ts_name'],
            'icd9_yb_code': icd,
            'icd9_yb_name': yb_full_name or t['ts_icd_name'],
            'icd9_gl_code': gl_code,
            'icd9_gl_name': gl_full_name,
        })
    print(f"  Direct ICD-9 links: {len(ts_icd_matches)}")

    # ============================================================
    # MAPPING 2: 立项指南 → 技术规范 (名称模糊匹配)
    # ============================================================
    print("\n--- Mapping 2: 立项指南 → 技术规范 ---")
    pg_ts_matches = build_similarity_index(
        pg_items, 'pg_name',
        ts_items, 'ts_name',
        threshold=0.55
    )
    print(f"  Name matches (threshold=0.55): {len(pg_ts_matches)}")

    # Score distribution
    score_bins = defaultdict(int)
    for m in pg_ts_matches:
        bin_key = f"{int(m['score']*10)/10:.1f}"
        score_bins[bin_key] += 1
    for k in sorted(score_bins.keys(), reverse=True):
        print(f"    Score {k}: {score_bins[k]}")

    # ============================================================
    # MAPPING 3: 上海价格 → 立项指南 (名称模糊匹配)
    # ============================================================
    print("\n--- Mapping 3: 上海价格 → 立项指南 ---")
    sh_pg_matches = build_similarity_index(
        sh_items, 'sh_full_name',
        pg_items, 'pg_name',
        threshold=0.5
    )
    print(f"  Name matches (threshold=0.5): {len(sh_pg_matches)}")

    # Only consider items with prices
    sh_with_price = [(i, idx) for idx, i in enumerate(sh_items) if i['sh_price']]
    print(f"  Shanghai items with prices: {len(sh_with_price)}")

    # ============================================================
    # BUILD FINAL TABLE
    # ============================================================
    print("\n--- Building final mapping table ---")

    # Create lookup dicts
    pg_ts_lookup = {}  # pg_idx -> ts_idx
    for m in pg_ts_matches:
        pg_ts_lookup[m['idx_a']] = {'idx': m['idx_b'], 'score': m['score']}

    sh_pg_lookup = {}  # sh_idx -> pg_idx
    for m in sh_pg_matches:
        sh_pg_lookup[m['idx_a']] = {'idx': m['idx_b'], 'score': m['score']}

    # Build rows
    output_rows = []

    # First pass: Shanghai prices → everything
    for sh_idx, sh in enumerate(sh_items):
        row = {
            # Shanghai
            'SH_编码': sh['sh_code'],
            'SH_名称': sh['sh_full_name'],
            'SH_内涵': sh['sh_desc'],
            'SH_单位': sh['sh_unit'],
            'SH_价格': sh['sh_price'],
            'SH_说明': sh['sh_notes'],
            # Match scores
            'SH→PG_匹配分': '',
            'PG→TS_匹配分': '',
            # Pricing guide
            'PG_序号': '',
            'PG_分类': '',
            'PG_名称': '',
            'PG_服务产出': '',
            'PG_价格构成': '',
            'PG_计价单位': '',
            # Tech specs
            'TS_编码': '',
            'TS_名称': '',
            'TS_内涵': '',
            # ICD-9
            'ICD9_医保编码': '',
            'ICD9_医保名称': '',
            'ICD9_国临编码': '',
            'ICD9_国临名称': '',
        }

        # Link SH → PG
        if sh_idx in sh_pg_lookup:
            pg_info = sh_pg_lookup[sh_idx]
            pg_idx = pg_info['idx']
            pg = pg_items[pg_idx]
            row['SH→PG_匹配分'] = f"{pg_info['score']:.2f}"
            row['PG_序号'] = pg['pg_seq']
            row['PG_分类'] = pg['pg_category']
            row['PG_名称'] = pg['pg_name']
            row['PG_服务产出'] = pg['pg_output']
            row['PG_价格构成'] = pg['pg_cost_structure']
            row['PG_计价单位'] = pg['pg_unit']

            # Link PG → TS
            if pg_idx in pg_ts_lookup:
                ts_info = pg_ts_lookup[pg_idx]
                ts_idx = ts_info['idx']
                ts = ts_items[ts_idx]
                row['PG→TS_匹配分'] = f"{ts_info['score']:.2f}"
                row['TS_编码'] = ts['ts_code']
                row['TS_名称'] = ts['ts_name']
                row['TS_内涵'] = ts['ts_desc']

                # Link TS → ICD-9 (from ts_icd_matches)
                for tm in ts_icd_matches:
                    if tm['ts_code'] == ts['ts_code']:
                        row['ICD9_医保编码'] = tm['icd9_yb_code']
                        row['ICD9_医保名称'] = tm['icd9_yb_name']
                        row['ICD9_国临编码'] = tm['icd9_gl_code']
                        row['ICD9_国临名称'] = tm['icd9_gl_name']
                        break

        output_rows.append(row)

    # ============================================================
    # PHASE 4: 输出
    # ============================================================
    print(f"\nTotal output rows: {len(output_rows)}")

    # Count various match types
    sh_pg_matched = sum(1 for r in output_rows if r['SH→PG_匹配分'])
    pg_ts_matched = sum(1 for r in output_rows if r['PG→TS_匹配分'])
    icd_matched = sum(1 for r in output_rows if r['ICD9_医保编码'])

    print(f"  SH→PG 已匹配: {sh_pg_matched}")
    print(f"  PG→TS 已匹配: {pg_ts_matched}")
    print(f"  TS→ICD9 已匹配: {icd_matched}")

    # Save as Excel
    df = pd.DataFrame(output_rows)
    # Sort: matched first, then unmatched
    df['_has_match'] = df['SH→PG_匹配分'].apply(lambda x: 3 if x else 0) + \
                        df['ICD9_医保编码'].apply(lambda x: 1 if x else 0)
    df = df.sort_values('_has_match', ascending=False)
    df = df.drop(columns=['_has_match'])

    outpath = f'{base}/四方映射表.xlsx'
    with pd.ExcelWriter(outpath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='四方映射', index=False)

        # Also save summary stats
        summary = pd.DataFrame([
            {'指标': '上海旧价格总数', '数值': len(sh_items)},
            {'指标': '上海有价格项目数', '数值': sum(1 for i in sh_items if i['sh_price'])},
            {'指标': '国家立项指南项目数', '数值': len(pg_items)},
            {'指标': '2023技术规范项目数', '数值': len(ts_items)},
            {'指标': '技术规范含ICD9项目数', '数值': len(ts_with_icd)},
            {'指标': 'ICD9国临版编码数', '数值': len(guolin_codes)},
            {'指标': 'ICD9对照表条目数', '数值': len(duizhao)},
            {'指标': 'SH→PG匹配数', '数值': sh_pg_matched},
            {'指标': 'PG→TS匹配数', '数值': pg_ts_matched},
            {'指标': 'TS→ICD9匹配数', '数值': icd_matched},
            {'指标': '四方全链路匹配数', '数值': sum(1 for r in output_rows if r['SH→PG_匹配分'] and r['PG→TS_匹配分'] and r['ICD9_医保编码'])},
        ])
        summary.to_excel(writer, sheet_name='匹配统计', index=False)

    print(f"\n[OK] Output saved to: {outpath}")

    # Save detailed match lists for review
    match_details = {
        'pg_ts_matches': pg_ts_matches[:100],
        'sh_pg_matches': sh_pg_matches[:100],
        'ts_icd_count': len(ts_icd_matches),
    }
    with open(f'{base}/_match_details.json', 'w', encoding='utf-8') as f:
        json.dump(match_details, f, ensure_ascii=False, indent=2, default=str)

    return output_rows


if __name__ == '__main__':
    rows = main()
