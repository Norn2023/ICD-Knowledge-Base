#!/usr/bin/env python3
"""
DRG 2.0 CC/MCC 提取器
从 PDF 提取表3-1-1（DRG分组+严重度）和表6-3（CC/MCC排除表）
运行：python extract_cc_mcc.py
"""

import sqlite3
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
DIR = os.path.dirname(__file__)
DRG_PDF = "按病组（DRG）付费分组方案（2.0版）.pdf"


def extract_adrg_full(conn):
    """从 PDF 页39-48 提取表2-1-1：完整 ADRG 列表（409个）"""
    import pdfplumber

    print("=" * 60)
    print("提取完整 ADRG 列表（表2-1-1）")
    print("=" * 60)

    adrg_list = []

    with pdfplumber.open(os.path.join(DIR, DRG_PDF)) as pdf:
        for pn in range(38, 48):  # Pages 39-48 only (表2-1-1 ends before 表3-1-1)
            text = pdf.pages[pn].extract_text() or ""
            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                # Format: "ADRG编码 ADRG名称"
                # ADRG codes are 3 chars (AA1) or 4 chars (AH1, BB4, etc.)
                # DRG codes are 4-5 chars (AA19, BB45) - skip those
                m = re.match(r'^([A-Z]{1,2}\d{1,2})\s+(.+)', line)
                if m:
                    code = m.group(1)
                    name = m.group(2).strip()
                    # ADRG codes are short and don't contain severity info
                    if not re.search(r'严重|一般|不伴|合并症', name):
                        if len(code) <= 4 and len(name) >= 2:
                            if '编码' not in code and '名称' not in name and '序号' not in line:
                                adrg_list.append((code, name))

    print(f"找到 ADRG: {len(adrg_list)}")
    if adrg_list:
        print(f"  示例: {adrg_list[0]} ... {adrg_list[-1]}")

    # Insert into DB
    cursor = conn.cursor()
    # Don't delete existing if already populated, but add missing ones
    existing = set()
    for row in cursor.execute("SELECT adrg_code FROM drg_adrg").fetchall():
        existing.add(row[0])

    new_count = 0
    for code, name in adrg_list:
        if code not in existing:
            cursor.execute(
                "INSERT OR IGNORE INTO drg_adrg (mdc_id, adrg_code, name, type) VALUES (NULL,?,?,'medical')",
                (code, name)
            )
            new_count += 1

    conn.commit()
    total = cursor.execute("SELECT COUNT(*) FROM drg_adrg").fetchone()[0]
    print(f"新增: {new_count}, 总计: {total}")
    return total


def extract_drg_groups(conn):
    """从 PDF 页49-64 提取表3-1-1：DRG 分组（含MCC/CC）"""
    import pdfplumber

    print("=" * 60)
    print("提取 DRG 分组（表3-1-1，含MCC/CC）")
    print("=" * 60)

    drg_list = []

    with pdfplumber.open(os.path.join(DIR, DRG_PDF)) as pdf:
        # Pages 49-64 (0-indexed: 48-63)
        for pn in range(48, 64):
            text = pdf.pages[pn].extract_text() or ""

            # Parse DRG rows: "ADRG DRG  DRG名称" format
            # Pattern: "XX1 XX11 名称，伴严重/一般/不伴合并症或并发症"
            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                # Match DRG pattern: 2-3 uppercase + digit, space, 2-3 uppercase + 2 digits
                # Example: "BR1 BR11 脑卒中，伴严重合并症或并发症"
                m = re.match(r'([A-Z]{1,2}\d{1,2})\s+([A-Z]{1,2}\d{2})\s+(.+)', line)
                if m:
                    adrg_code = m.group(1)
                    drg_code = m.group(2)
                    drg_name = m.group(3).strip()

                    # Determine severity (order matters!)
                    if '不伴' in drg_name:
                        severity = 'noCC'
                    elif '严重' in drg_name:
                        severity = 'MCC'
                    elif '一般' in drg_name:
                        severity = 'CC'
                    elif '合并' in drg_name:
                        severity = 'CC'
                    else:
                        severity = 'unspecified'

                    drg_list.append((adrg_code, drg_code, drg_name, severity))

    print(f"找到 DRG 分组: {len(drg_list)}")
    if drg_list:
        print(f"  示例: {drg_list[5]}")
        print(f"  末条: {drg_list[-1]}")

    # Count by severity
    sev_counts = {}
    for _, _, _, s in drg_list:
        sev_counts[s] = sev_counts.get(s, 0) + 1
    for s, c in sorted(sev_counts.items()):
        print(f"  {s}: {c}")

    # Flush old data
    cursor = conn.cursor()
    cursor.execute("DELETE FROM drg_procedure_map")
    cursor.execute("DELETE FROM drg_diagnosis_map")
    cursor.execute("DELETE FROM drg_groups")

    # Ensure drg_groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drg_groups (
            id INTEGER PRIMARY KEY,
            adrg_id INTEGER REFERENCES drg_adrg(id),
            drg_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('MCC','CC','noCC','unspecified')),
            weight REAL,
            avg_cost REAL,
            avg_days REAL
        )
    """)

    # Match ADRG IDs
    adrg_lookup = {}
    for row in cursor.execute("SELECT id, adrg_code FROM drg_adrg").fetchall():
        adrg_lookup[row[1]] = row[0]

    # Insert DRG groups
    batch = []
    matched = 0
    for adrg_code, drg_code, drg_name, sev in drg_list:
        adrg_id = adrg_lookup.get(adrg_code)
        if adrg_id:
            batch.append((adrg_id, drg_code, drg_name, sev))
            matched += 1
        else:
            batch.append((None, drg_code, drg_name, sev))

        if len(batch) >= 100:
            cursor.executemany(
                "INSERT OR IGNORE INTO drg_groups (adrg_id, drg_code, name, severity) VALUES (?,?,?,?)",
                batch
            )
            conn.commit()
            batch = []

    if batch:
        cursor.executemany(
            "INSERT OR IGNORE INTO drg_groups (adrg_id, drg_code, name, severity) VALUES (?,?,?,?)",
            batch
        )
        conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM drg_groups").fetchone()[0]
    print(f"已入库 DRG: {count} (其中 {matched} 已匹配 ADRG)")

    # Sample of each severity
    for sev in ['MCC', 'CC', 'noCC', 'unspecified']:
        sample = cursor.execute(
            "SELECT drg_code, name FROM drg_groups WHERE severity=? LIMIT 2", (sev,)
        ).fetchall()
        if sample:
            print(f"  [{sev}] {sample[0][0]} {sample[0][1]}")
            if len(sample) > 1:
                print(f"        {sample[1][0]} {sample[1][1]}")

    return count


def extract_cc_exclusions(conn):
    """从 PDF 页1486-1834 提取表6-3：CC/MCC 排除表"""
    import pdfplumber

    print("\n" + "=" * 60)
    print("提取 CC/MCC 排除表（表6-3）")
    print("=" * 60)

    cursor = conn.cursor()

    # Create exclusion table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cc_exclusions (
            id INTEGER PRIMARY KEY,
            icd10_code TEXT NOT NULL,
            icd10_name TEXT,
            excluded_table TEXT,
            icd10_id INTEGER REFERENCES icd10_codes(id)
        )
    """)
    cursor.execute("DELETE FROM cc_exclusions")

    exclusions = []
    current_code = None
    current_name = ""
    current_excl = ""

    with pdfplumber.open(os.path.join(DIR, DRG_PDF)) as pdf:
        for pn in range(1485, len(pdf.pages)):
            text = pdf.pages[pn].extract_text() or ""

            if '疾病编码' in text and '排除内容' in text:
                # Header page - save any pending entry, skip
                if current_code:
                    exclusions.append((current_code, current_name.strip(), current_excl.strip()))
                    current_code = None
                    current_name = ""
                    current_excl = ""
                continue

            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line or len(line) < 8:
                    continue
                if '1485' in line or line.startswith('3、') or line.startswith('3.'):
                    continue

                # Try to match ICD-10 code at start of line
                m = re.match(r'([A-Z]\d{2}\.\w+(?:x\d+)?)\s+(.+)', line)
                if m:
                    # Save previous entry
                    if current_code:
                        exclusions.append((current_code, current_name.strip(), current_excl.strip()))

                    current_code = m.group(1)
                    rest = m.group(2)

                    # Extract exclusion table references
                    table_refs = re.findall(r'表6-3-\d+', rest)
                    if table_refs:
                        current_excl = ','.join(table_refs)
                        # Remove table refs from name
                        current_name = rest
                        for t in table_refs:
                            current_name = current_name.replace(t, '').strip()
                        # Clean up trailing spaces
                        current_name = re.sub(r'\s+', ' ', current_name).strip()
                    else:
                        current_name = rest
                        current_excl = ""
                else:
                    # Continuation of previous entry's name or exclusion
                    if current_code:
                        # Check if it's just a page number/continuation
                        if '表6-3-' in line:
                            current_excl += ',' + line.strip()
                        elif not line.isdigit() and line != '1485':
                            current_name += line

            if (pn + 1) % 50 == 0:
                print(f"  进度: {pn+1}/{len(pdf.pages)}, 已收集 {len(exclusions)}")

        # Don't forget the last entry
        if current_code:
            exclusions.append((current_code, current_name.strip(), current_excl.strip()))

    print(f"找到排除记录: {len(exclusions)}")

    if exclusions:
        print(f"  示例: {exclusions[0]}")
        print(f"  示例: {exclusions[5]}")
        print(f"  末条: {exclusions[-1]}")

    # Insert
    batch = []
    matched = 0
    for code, name, excluded in exclusions:
        # Find ICD-10 ID
        icd10_row = cursor.execute("SELECT id FROM icd10_codes WHERE code=?", (code,)).fetchone()
        icd10_id = icd10_row[0] if icd10_row else None
        if icd10_id:
            matched += 1

        batch.append((code, name[:100] if name else '', excluded, icd10_id))

        if len(batch) >= 500:
            cursor.executemany(
                "INSERT INTO cc_exclusions (icd10_code, icd10_name, excluded_table, icd10_id) VALUES (?,?,?,?)",
                batch
            )
            conn.commit()
            batch = []

    if batch:
        cursor.executemany(
            "INSERT INTO cc_exclusions (icd10_code, icd10_name, excluded_table, icd10_id) VALUES (?,?,?,?)",
            batch
        )
        conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM cc_exclusions").fetchone()[0]
    print(f"已入库排除记录: {count} (其中 {matched} 已关联 ICD-10)")

    return count


def main():
    print("DRG CC/MCC 提取器\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")

    try:
        n_adrg = extract_adrg_full(conn)
        n_drg = extract_drg_groups(conn)
        n_excl = extract_cc_exclusions(conn)

        # Verify
        cur = conn.cursor()

        print("\n" + "=" * 60)
        print("验证结果")
        print("=" * 60)

        # DRG stats
        total_drg = cur.execute("SELECT COUNT(*) FROM drg_groups").fetchone()[0]
        mcc_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='MCC'").fetchone()[0]
        cc_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='CC'").fetchone()[0]
        nocc_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='noCC'").fetchone()[0]
        unsp_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='unspecified'").fetchone()[0]

        print(f"\nDRG 分组: {total_drg}")
        print(f"  MCC: {mcc_count}    CC: {cc_count}    noCC: {nocc_count}    unspecified: {unsp_count}")

        print(f"\nCC/MCC 排除记录: {n_excl}")

        # Show ADRG with most DRG splits
        print("\nADRG DRG 拆分示例:")
        for row in cur.execute("""
            SELECT a.adrg_code, a.name, COUNT(dg.id) as n, GROUP_CONCAT(dg.drg_code) as codes
            FROM drg_groups dg
            JOIN drg_adrg a ON dg.adrg_id=a.id
            GROUP BY a.id
            ORDER BY n DESC LIMIT 5
        """).fetchall():
            print(f"  {row[0]} {row[1]}: {row[2]} 个 DRG ({row[3]})")

        print(f"\n[OK] 完成！")
        print(f"  python generate_md.py       -> 刷新笔记")
        print(f"  python generate_web_json.py -> 刷新网页")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
