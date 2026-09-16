#!/usr/bin/env python3
"""
DRG 2.0 + DIP 2.0 导入器
从 PDF 解析 DRG 分组方案和 DIP 病种库
运行：python import_drg_dip.py
"""

import sqlite3
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
DIR = os.path.dirname(__file__)

# ═══════════════════════════════════════
# DIP 2.0 导入（表格格式，简单）
# ═══════════════════════════════════════

def import_dip(conn):
    """从 DIP PDF 导入病种库"""
    import pdfplumber

    print("=" * 60)
    print("导入 DIP 2.0 病种库")
    print("=" * 60)

    path = os.path.join(DIR, "按病种分值（DIP）付费病种库（2.0版）202407.pdf")
    if not os.path.exists(path):
        print("[SKIP] 文件不存在")
        return 0

    cursor = conn.cursor()
    cursor.execute("DELETE FROM dip_groups")

    all_rows = []
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}")
        empty_pages = 0

        for i in range(total):
            tables = pdf.pages[i].extract_tables()
            if not tables:
                empty_pages += 1
                continue

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # 跳过表头
                for row in table[1:]:
                    if not row or len(row) < 2:
                        continue
                    # 7列: 编号, 主要诊断代码, 主要诊断名称, 主要手术操作代码, 主要手术操作名称, 相关手术操作代码, 相关手术操作名称
                    if len(row) >= 3 and row[0] and row[0].strip().isdigit():
                        dip_no = row[0].strip()
                        diag_code = (row[1] or "").strip()
                        diag_name = (row[2] or "").strip()
                        proc_code = (row[3] or "").strip() if len(row) > 3 else ""
                        proc_name = (row[4] or "").strip() if len(row) > 4 else ""
                        related_code = (row[5] or "").strip() if len(row) > 5 else ""
                        related_name = (row[6] or "").strip() if len(row) > 6 else ""

                        if diag_code:
                            all_rows.append((
                                dip_no, diag_code, diag_name,
                                proc_code, proc_name,
                                related_code, related_name
                            ))
            if (i+1) % 50 == 0:
                print(f"  进度: {i+1}/{total} 页, 已收集 {len(all_rows)} 条")

    print(f"空页数: {empty_pages}")
    print(f"解析行数: {len(all_rows)}")

    # 批量写入
    batch = []
    for dip_no, dc, dn, pc, pn, rc, rn in all_rows:
        # 匹配 ICD 编码 ID
        icd10_id = cursor.execute(
            "SELECT id FROM icd10_codes WHERE code=?", (dc,)
        ).fetchone()
        icd9_id = cursor.execute(
            "SELECT id FROM icd9_codes WHERE code=?", (pc,)
        ).fetchone() if pc else None

        batch.append((
            f"DIP{dip_no}", dn[:50] if dn else "",
            icd10_id[0] if icd10_id else None,
            icd9_id[0] if icd9_id else None,
            0, 0  # avg_cost, weight (not in 2.0 PDF)
        ))

        if len(batch) >= 500:
            cursor.executemany(
                "INSERT OR IGNORE INTO dip_groups (dip_code, name, icd10_primary_id, icd9_primary_id, avg_cost, weight) VALUES (?,?,?,?,?,?)",
                batch
            )
            conn.commit()
            batch = []

    if batch:
        cursor.executemany(
            "INSERT OR IGNORE INTO dip_groups (dip_code, name, icd10_primary_id, icd9_primary_id, avg_cost, weight) VALUES (?,?,?,?,?,?)",
            batch
        )
        conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM dip_groups").fetchone()[0]
    print(f"已导入 {count} 个 DIP 病种")
    return count


# ═══════════════════════════════════════
# DRG 2.0 导入（文本流格式，需要解析）
# ═══════════════════════════════════════

def import_drg(conn):
    """从 DRG PDF 解析 ADRG 分组和主诊表"""
    import pdfplumber

    print("\n" + "=" * 60)
    print("导入 DRG 2.0 分组方案")
    print("=" * 60)

    path = os.path.join(DIR, "按病组（DRG）付费分组方案（2.0版）.pdf")
    if not os.path.exists(path):
        print("[SKIP] 文件不存在")
        return 0

    cursor = conn.cursor()

    # Allow NULL for mdc_id (we can't always determine MDC)
    cursor.execute("PRAGMA foreign_keys = OFF")
    try:
        cursor.execute("ALTER TABLE drg_adrg RENAME TO drg_adrg_old")
        cursor.execute("""
            CREATE TABLE drg_adrg (
                id INTEGER PRIMARY KEY,
                mdc_id INTEGER REFERENCES drg_mdc(id),
                adrg_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('surgical','medical','other'))
            )
        """)
        cursor.execute("INSERT INTO drg_adrg SELECT id, mdc_id, adrg_code, name, type FROM drg_adrg_old")
        cursor.execute("DROP TABLE drg_adrg_old")
    except sqlite3.OperationalError:
        # Already altered or table doesn't exist yet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drg_adrg (
                id INTEGER PRIMARY KEY,
                mdc_id INTEGER REFERENCES drg_mdc(id),
                adrg_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('surgical','medical','other'))
            )
        """)
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()

    # DRG PDF 结构（通过深探发现）：
    # - 页94-664: ADRG 定义，格式为 "ADRG_CODE ADRG_NAME\n包含以下主要诊断：\nICD10_CODE ICD10_NAME ..."
    # - 页665-1485: MDC 主诊表，格式为 "MDC_NAME\n包含以下主要诊断：\n..."
    # - 页1486-1834: 附录

    print("提取全文...")
    full_text_parts = []
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for i in range(total):
            text = pdf.pages[i].extract_text() or ""
            full_text_parts.append(text)
            if (i+1) % 200 == 0:
                print(f"  提取进度: {i+1}/{total}")

    full_text = "\n".join(full_text_parts)
    print(f"总字符数: {len(full_text):,}")

    # ── Clean up old DRG data ──
    cursor.execute("DELETE FROM drg_procedure_map")
    cursor.execute("DELETE FROM drg_diagnosis_map")
    cursor.execute("DELETE FROM drg_groups")
    cursor.execute("DELETE FROM adrg_diagnosis_map")
    cursor.execute("DELETE FROM mdc_diagnosis_map")
    cursor.execute("DELETE FROM drg_adrg")
    cursor.execute("DELETE FROM drg_mdc")

    # ── Step 1: Find MDCs ──
    # MDC pattern: "MDCA 神经系统疾病及功能障碍" like
    mdc_pattern = re.compile(r'(MDC[A-Z])\s+(\S[^\n]{0,50})')
    mdcs_found = {}
    for m in mdc_pattern.finditer(full_text):
        code = m.group(1)
        name = m.group(2).strip()
        if code not in mdcs_found:
            mdcs_found[code] = name

    print(f"找到 MDC: {len(mdcs_found)}")

    # Insert MDCs
    mdc_id_map = {}
    for code, name in mdcs_found.items():
        cursor.execute(
            "INSERT INTO drg_mdc (mdc_code, name) VALUES (?,?)",
            (code, name)
        )
        mdc_id_map[code] = cursor.lastrowid

    # ── Step 2: Find ADRGs with their diagnosis lists ──
    # ADRG patterns: 2-3 letter combos followed by Chinese text
    # Like: "BB4 伴创伤诊断的颅脑手术\n包含以下主要诊断："
    # The ADRG code is usually: [A-Z]{1,2}[A-Z]?[1-9][0-9]? (like BB4, CD1, FW1, etc.)
    adrg_pattern = re.compile(
        r'([A-Z]{1,2}[1-9]\d?)\s+(\S[^\n]{0,60})\s*\n包含以下主要诊断[：:]\s*\n'
        r'((?:[A-Z]\d[^\n]*\n?)+?)'
        r'(?=\n[A-Z]{1,2}[1-9]\d?\s|\nMDC|\Z)',
        re.MULTILINE
    )

    # Simpler: find each ADRG block
    # "BB4 伴创伤诊断的颅脑手术\n包含以下主要诊断：\nI61.0 ... I63.9 ..."
    lines = full_text.split('\n')
    adrg_blocks = []

    current_adrg = None
    current_diags = []
    in_diag_list = False

    # Pattern for ADRG header: starts with 1-2 uppercase letters + 1-2 digits + space + Chinese
    adrg_header = re.compile(r'^([A-Z]{1,2}\d{1,2})\s+(.+)')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        m = adrg_header.match(line)
        if m:
            # Save previous block
            if current_adrg and current_diags:
                adrg_blocks.append((current_adrg[0], current_adrg[1], current_diags))

            current_adrg = (m.group(1), m.group(2))
            current_diags = []
            in_diag_list = False
            continue

        if current_adrg and "包含以下主要诊断" in line:
            in_diag_list = True
            continue

        if in_diag_list:
            # Check if we hit another section
            if line.startswith("MDC") and "疾病" in line:
                # Save and continue
                if current_adrg and current_diags:
                    adrg_blocks.append((current_adrg[0], current_adrg[1], current_diags))
                current_diags = []
                in_diag_list = False
                continue

            # Extract ICD-10 codes
            # Format: "I21.001 急性前壁心肌梗死" or "A18.818+I79.8* 结核性腹主动脉炎"
            codes = re.findall(r'([A-Z]\d{2}\.\w{0,6}(?:\+[A-Z]\d{2}\.\w{0,6}\*)?)', line)
            if codes:
                for c in codes:
                    current_diags.append(c)

    # Don't forget the last block
    if current_adrg and current_diags:
        adrg_blocks.append((current_adrg[0], current_adrg[1], current_diags))

    print(f"找到 ADRG 分组: {len(adrg_blocks)}")
    if adrg_blocks:
        print(f"  示例: {adrg_blocks[0][0]} {adrg_blocks[0][1]} ({len(adrg_blocks[0][2])} 诊断)")

    # ── Step 3: Map ADRGs to MDCs ──
    # Use first letter(s) of ADRG to infer MDC
    # This is approximate: BB4->MDCB, CD1->MDCC, DU1->MDCD, etc.
    # Build a reverse map from the MDC data in the PDF

    # Strategy: find which MDC code appears closest to each ADRG in the text
    mdc_positions = [(m.start(), m.group(1)) for m in mdc_pattern.finditer(full_text)]

    def find_nearest_mdc(pos):
        best_mdc = None
        best_dist = float('inf')
        for mdc_pos, mdc_code in mdc_positions:
            if mdc_pos <= pos:
                dist = pos - mdc_pos
                if dist < best_dist:
                    best_dist = dist
                    best_mdc = mdc_code
        return best_mdc

    # Find each ADRG position in text
    adrg_positions = {}
    for adrg_code, _, _ in adrg_blocks:
        # Search for the exact ADRG code occurrence
        pos = full_text.find(adrg_code + ' ')
        if pos >= 0:
            adrg_positions[adrg_code] = pos

    # Deduplicate ADRG blocks (same ADRG may appear multiple times)
    seen_adrg = {}
    for adrg_code, adrg_name, diags in adrg_blocks:
        if adrg_code not in seen_adrg:
            seen_adrg[adrg_code] = [adrg_code, adrg_name, list(diags)]
        else:
            # Merge diagnosis lists
            seen_adrg[adrg_code][2].extend(diags)
    adrg_blocks = list(seen_adrg.values())
    print(f"去重后 ADRG: {len(adrg_blocks)}")

    # Insert ADRGs into DB
    adrg_id_map = {}
    for adrg_code, adrg_name, diags in adrg_blocks:
        mdc_id = None

        # Try inferring from ADRG position
        pos = adrg_positions.get(adrg_code, 0)
        mdc_from_pos = find_nearest_mdc(pos)
        if mdc_from_pos:
            mdc_id = mdc_id_map.get(mdc_from_pos)

        if not mdc_id:
            # Fallback: use first letters of ADRG to guess MDC
            prefix = re.match(r'([A-Z]+)', adrg_code)
            if prefix:
                letter = prefix.group(1)[0]  # First letter
                for mdc_code, mid in mdc_id_map.items():
                    if mdc_code.endswith(letter):
                        mdc_id = mid
                        break

        cursor.execute(
            "INSERT INTO drg_adrg (mdc_id, adrg_code, name, type) VALUES (?,?,?,?)",
            (mdc_id, adrg_code, adrg_name, 'medical')
        )
        adrg_id_map[adrg_code] = cursor.lastrowid

    adrg_count = cursor.execute("SELECT COUNT(*) FROM drg_adrg").fetchone()[0]
    print(f"ADRG 入库: {adrg_count}")
    if mdc_id is None:
        null_count = cursor.execute("SELECT COUNT(*) FROM drg_adrg WHERE mdc_id IS NULL").fetchone()[0]
        print(f"  其中 MDC 未匹配: {null_count}")

    # ── Step 4: Insert diagnosis mappings ──
    dx_map_count = 0
    batch = []
    for adrg_code, adrg_name, diags in adrg_blocks:
        adrg_id = adrg_id_map.get(adrg_code)
        if not adrg_id:
            continue

        for icd10_code in diags:
            # Find ICD-10 code in DB (try exact match, then base code)
            icd10_row = cursor.execute(
                "SELECT id FROM icd10_codes WHERE code=?", (icd10_code,)
            ).fetchone()

            if not icd10_row:
                # Try without suffix (e.g., "I21.001" -> "I21.0")
                base = re.match(r'([A-Z]\d{2}\.\d)', icd10_code)
                if base:
                    icd10_row = cursor.execute(
                        "SELECT id FROM icd10_codes WHERE code LIKE ?",
                        (base.group(1) + '%',)
                    ).fetchone()

            if icd10_row:
                batch.append((adrg_id, icd10_row[0]))
                dx_map_count += 1

        if len(batch) >= 500:
            cursor.executemany(
                "INSERT INTO adrg_diagnosis_map (adrg_id, icd10_id) VALUES (?,?)",
                batch
            )
            conn.commit()
            batch = []

    if batch:
        cursor.executemany(
            "INSERT INTO adrg_diagnosis_map (adrg_id, icd10_id) VALUES (?,?)",
            batch
        )
        conn.commit()

    print(f"诊断映射: {dx_map_count}")

    # ── Also find MDC diagnosis tables from pages 665+ ──
    print("\n解析 MDC 主诊表...")
    # Pages 665+ use format: "MDCX 疾病名称\n包含以下主要诊断：\n..."

    mdc_diag_pattern = re.compile(
        r'(MDC[A-Z])\s+(\S[^\n]{0,50})\s*\n包含以下主要诊断[：:]\s*\n'
        r'((?:[A-Z]\d[^\n]*\n?)+?)(?=\nMDC|\Z)',
        re.MULTILINE
    )

    mdc_diag_map = {}
    for m in mdc_diag_pattern.finditer(full_text):
        mdc_code = m.group(1)
        mdc_name = m.group(2).strip()
        diag_text = m.group(3)

        codes = re.findall(r'([A-Z]\d{2}\.\w{0,6}(?:\+[A-Z]\d{2}\.\w{0,6}\*)?)', diag_text)
        mdc_diag_map[mdc_code] = (mdc_name, codes)

    print(f"MDC 主诊表: {len(mdc_diag_map)} 个")

    # Store MDC diagnosis tables
    mdc_diag_count = 0
    batch = []
    for mdc_code, (mdc_name, diags) in mdc_diag_map.items():
        mdc_id = mdc_id_map.get(mdc_code)
        if not mdc_id:
            continue
        for icd10_code in diags:
            icd10_row = cursor.execute(
                "SELECT id FROM icd10_codes WHERE code=?", (icd10_code,)
            ).fetchone()
            if not icd10_row:
                base = re.match(r'([A-Z]\d{2}\.\d)', icd10_code)
                if base:
                    icd10_row = cursor.execute(
                        "SELECT id FROM icd10_codes WHERE code LIKE ?",
                        (base.group(1) + '%',)
                    ).fetchone()
            if icd10_row:
                batch.append((mdc_id, icd10_row[0]))
                mdc_diag_count += 1

        if len(batch) >= 500:
            cursor.executemany(
                "INSERT INTO mdc_diagnosis_map (mdc_id, icd10_id) VALUES (?,?)",
                batch
            )
            conn.commit()
            batch = []

    if batch:
        cursor.executemany(
            "INSERT INTO mdc_diagnosis_map (mdc_id, icd10_id) VALUES (?,?)",
            batch
        )
        conn.commit()

    print(f"MDC 诊断映射: {mdc_diag_count}")

    # Count results
    final_adrg = cursor.execute("SELECT COUNT(*) FROM drg_adrg").fetchone()[0]
    final_mdc = cursor.execute("SELECT COUNT(*) FROM drg_mdc").fetchone()[0]

    print(f"\nDRG 导入完成: {final_mdc} MDC · {final_adrg} ADRG · {dx_map_count} 诊断映射")
    return final_adrg


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    print("DRG/DIP 导入器\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")

    try:
        # Create mapping tables if not exist
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adrg_diagnosis_map (
                id INTEGER PRIMARY KEY,
                adrg_id INTEGER NOT NULL REFERENCES drg_adrg(id),
                icd10_id INTEGER NOT NULL REFERENCES icd10_codes(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mdc_diagnosis_map (
                id INTEGER PRIMARY KEY,
                mdc_id INTEGER NOT NULL REFERENCES drg_mdc(id),
                icd10_id INTEGER NOT NULL REFERENCES icd10_codes(id)
            )
        """)
        conn.commit()

        dip_count = import_dip(conn)
        drg_count = import_drg(conn)

        print("\n" + "=" * 60)
        print("导入完成！")
        print(f"  DRG ADRG: {drg_count}")
        print(f"  DIP 病种: {dip_count}")
        print(f"\n下一步:")
        print(f"  python generate_md.py       → 刷新笔记")
        print(f"  python generate_web_json.py → 刷新网页")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
