#!/usr/bin/env python3
"""
DRG 2.0 手术操作→ADRG 映射提取器
从 129 页 ADRG 定义中提取"包含以下主要手术或操作"列表
运行：python extract_procedures.py
"""

import sqlite3
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
DIR = os.path.dirname(__file__)
DRG_PDF = "按病组（DRG）付费分组方案（2.0版）.pdf"


def extract_procedure_mappings():
    """从 DP's DRG 定义页提取手术操作→ADRG 映射"""
    import pdfplumber

    print("=" * 60)
    print("提取 手术操作→ADRG 映射")
    print("=" * 60)

    with pdfplumber.open(os.path.join(DIR, DRG_PDF)) as pdf:
        adrg_proc_map = {}  # adrg_code -> [(icd9_code, icd9_name), ...]

        current_adrg = None
        in_proc_section = False
        found_adrg_header = False

        # Process pages 64-1033 (ADRG definitions)
        for pn in range(64, min(1034, len(pdf.pages))):
            text = pdf.pages[pn].extract_text() or ""
            if not text.strip():
                continue

            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect ADRG header: "XX1 Name" pattern
                # Like: "AA1 心肺移植" or "BB4 伴创伤诊断的颅脑手术"
                m = re.match(r'^([A-Z]{1,2}\d{1,2})\s+(.+)$', line)
                if m:
                    code = m.group(1)
                    name = m.group(2).strip()

                    # Skip things that look like ADRG but aren't
                    skip_words = ['编码', '名称', '序号', 'ADRG', 'DRG', 'MDC', '包含', '以下',
                                  '主要', '手术', '操作', '诊断', '页', '表', '四、']
                    if any(name.startswith(w) for w in skip_words):
                        # It might still be a valid ADRG if the name is a known one
                        pass
                    if len(code) >= 2 and len(code) <= 4 and len(name) > 1:
                        if not re.search(r'^\d|^表|^页', name):
                            # Save previous ADRG if we were in a proc section
                            current_adrg = code
                            found_adrg_header = True
                            in_proc_section = False
                            if code not in adrg_proc_map:
                                adrg_proc_map[code] = []
                            continue

                # Detect procedure section start
                if current_adrg and ('包含以下主要手术' in line or '主要手术或操作' in line):
                    in_proc_section = True
                    continue

                # Detect "包含以下主要诊断" -> exit proc section
                if current_adrg and in_proc_section and '包含以下主要诊断' in line:
                    in_proc_section = False
                    continue

                # Extract procedures in proc section
                if current_adrg and in_proc_section:
                    # ICD-9-CM-3 codes: 2 digits + dot + 0-2 digits + optional alphanumeric suffix
                    # Examples: "47.0900 阑尾切除术", "00.9500x001 心脏起搏器"
                    # Also: "38.3400 主动脉部分切除术伴吻合术"
                    icd9_pattern = re.compile(r'(\d{2,3}\.\w{2,6})\s+(.+?)(?=\s*\d{2,3}\.\w{2,6}\s+|$)')
                    matches = icd9_pattern.findall(line)

                    if matches:
                        for proc_code, proc_name in matches:
                            proc_name = proc_name.strip()
                            # Clean: remove trailing garbage
                            proc_name = re.sub(r'\s*\|\s*$', '', proc_name)
                            if len(proc_code) >= 4 and len(proc_name) >= 2:
                                adrg_proc_map[current_adrg].append((proc_code, proc_name))

            if (pn + 1) % 100 == 0:
                print(f"  进度: {pn+1}/1034, 已找到 {len(adrg_proc_map)} 个含手术的 ADRG")

    # Summary
    total_adrgs = len(adrg_proc_map)
    total_procs = sum(len(v) for v in adrg_proc_map.values())
    print(f"\n含手术映射的 ADRG: {total_adrgs}")
    print(f"手术映射总数: {total_procs}")

    if adrg_proc_map:
        # Show samples
        samples = [(k,v) for k,v in list(adrg_proc_map.items())[:3] if v]
        for code, procs in samples:
            print(f"  {code}: {len(procs)} procedures (e.g. {procs[0]})")

    return adrg_proc_map


def save_to_db(adrg_proc_map):
    """Save procedure mappings to database"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")
    cursor = conn.cursor()

    # Ensure table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adrg_procedure_map (
            id INTEGER PRIMARY KEY,
            adrg_id INTEGER NOT NULL REFERENCES drg_adrg(id),
            icd9_id INTEGER REFERENCES icd9_codes(id),
            icd9_code TEXT NOT NULL,
            icd9_name TEXT
        )
    """)
    cursor.execute("DELETE FROM adrg_procedure_map")

    # Lookup ADRG IDs
    adrg_lookup = {}
    for row in cursor.execute("SELECT id, adrg_code FROM drg_adrg").fetchall():
        adrg_lookup[row[1]] = row[0]

    # Lookup ICD-9 IDs
    icd9_lookup = {}
    for row in cursor.execute("SELECT id, code FROM icd9_codes").fetchall():
        icd9_lookup[row[1]] = row[0]

    batch = []
    total_inserted = 0
    matched_adrg = 0
    matched_icd9 = 0

    for adrg_code, procs in adrg_proc_map.items():
        adrg_id = adrg_lookup.get(adrg_code)
        if not adrg_id:
            continue
        matched_adrg += 1

        for proc_code, proc_name in procs:
            icd9_id = icd9_lookup.get(proc_code)
            if icd9_id:
                matched_icd9 += 1

            batch.append((adrg_id, icd9_id, proc_code, proc_name[:200] if proc_name else ''))
            total_inserted += 1

            if len(batch) >= 1000:
                cursor.executemany(
                    "INSERT INTO adrg_procedure_map (adrg_id, icd9_id, icd9_code, icd9_name) VALUES (?,?,?,?)",
                    batch
                )
                conn.commit()
                batch = []

    if batch:
        cursor.executemany(
            "INSERT INTO adrg_procedure_map (adrg_id, icd9_id, icd9_code, icd9_name) VALUES (?,?,?,?)",
            batch
        )
        conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM adrg_procedure_map").fetchone()[0]
    print(f"\n入库: {count} 条")
    print(f"  ADRG 匹配: {matched_adrg}")
    print(f"  ICD-9 匹配: {matched_icd9}")

    # Show top ADRGs by procedure count
    print("\n手术最多的 ADRG:")
    for row in cursor.execute("""
        SELECT a.adrg_code, a.name, COUNT(apm.id) as n
        FROM adrg_procedure_map apm
        JOIN drg_adrg a ON apm.adrg_id=a.id
        GROUP BY a.id
        ORDER BY n DESC LIMIT 8
    """).fetchall():
        print(f"  {row[0]} {row[1]}: {row[2]} 个手术")

    conn.close()
    return count


def main():
    print("DRG 手术操作映射提取器\n")

    adrg_proc_map = extract_procedure_mappings()
    if not adrg_proc_map:
        print("[ERROR] 未提取到数据")
        return

    count = save_to_db(adrg_proc_map)

    print(f"\n[OK] 完成！")
    print(f"  手术→ADRG 映射: {count} 条")
    print(f"\n现在全链路完整了：")
    print(f"  诊断 → ADRG → DRG(含MCC/CC)")
    print(f"  手术 → ADRG → DRG(含MCC/CC)")
    print(f"\n  python generate_md.py       -> 刷新笔记")
    print(f"  python generate_web_json.py -> 刷新网页")


if __name__ == "__main__":
    main()
