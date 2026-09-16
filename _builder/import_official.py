#!/usr/bin/env python3
"""
ICD 编码知识库 · 官方数据导入器
从医保局官网下载的 Excel(HTML) 文件导入 ICD-10 和 ICD-9 编码
运行：python import_official.py
"""

import sqlite3
import os
import sys
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
DIR = os.path.dirname(__file__)

# 文件名
ICD10_FILE = "ICD-10医保2(2026年5月从医保局官网下载）.xlsx"
ICD9_FILE = "ICD-9-CM3医保2(2026年5月从医保局官网下载）.xlsx"


def import_icd10(conn):
    """导入 ICD-10 疾病诊断编码"""
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

    print("\n" + "="*60)
    print("导入 ICD-10 疾病诊断编码")
    print("="*60)

    path = os.path.join(DIR, ICD10_FILE)
    if not os.path.exists(path):
        print(f"[ERROR] 文件不存在: {path}")
        return

    tables = pd.read_html(path)
    df = tables[0]

    # 列结构（医保局标准格式）：
    # 0: 章序号
    # 1: 章编码范围
    # 2: 章名称
    # 3: 节编码范围
    # 4: 节名称
    # 5: 类目编码
    # 6: 类目名称
    # 7: 亚目编码
    # 8: 亚目名称
    # 9: 诊断编码（完整）
    # 10: 诊断名称

    df.columns = ["chapter_no", "chapter_range", "chapter_name",
                  "section_range", "section_name",
                  "cat_code", "cat_name",
                  "sub_code", "sub_name",
                  "diag_code", "diag_name"]

    # 跳过表头行
    data = df.iloc[1:].copy()
    data = data.dropna(subset=["diag_code"])

    print(f"总行数（含表头）: {len(df)}")
    print(f"有效编码行数: {len(data)}")

    cursor = conn.cursor()

    # 清空旧数据
    cursor.execute("DELETE FROM case_procedures")
    cursor.execute("DELETE FROM case_diagnoses")
    cursor.execute("DELETE FROM cases")
    cursor.execute("DELETE FROM drg_procedure_map")
    cursor.execute("DELETE FROM drg_diagnosis_map")
    cursor.execute("DELETE FROM drg_groups")
    cursor.execute("DELETE FROM drg_adrg")
    cursor.execute("DELETE FROM drg_mdc")
    cursor.execute("DELETE FROM dip_groups")
    cursor.execute("DELETE FROM icd10_codes")
    cursor.execute("DELETE FROM icd10_sections")
    cursor.execute("DELETE FROM icd10_chapters")

    # 1. 导入章
    chapters = data[["chapter_no", "chapter_range", "chapter_name"]].drop_duplicates()
    chapter_map = {}
    for _, row in chapters.iterrows():
        folder = f"{int(float(row['chapter_no'])):02d}-{row['chapter_name']}({row['chapter_range']})"
        cursor.execute(
            "INSERT INTO icd10_chapters (chapter_no, code_range, name, folder_name) VALUES (?,?,?,?)",
            (int(float(row['chapter_no'])), str(row['chapter_range']), str(row['chapter_name']), folder)
        )
        chapter_map[str(row['chapter_range'])] = cursor.lastrowid
    print(f"章节: {len(chapter_map)}")

    # 2. 导入节
    sections = data[["chapter_range", "section_range", "section_name"]].drop_duplicates()
    section_map = {}
    sec_count = 0
    for _, row in sections.iterrows():
        ch_id = chapter_map.get(str(row['chapter_range']))
        if ch_id:
            cursor.execute(
                "INSERT INTO icd10_sections (chapter_id, code_range, name) VALUES (?,?,?)",
                (ch_id, str(row['section_range']), str(row['section_name']))
            )
            section_map[str(row['section_range'])] = cursor.lastrowid
            sec_count += 1
    print(f"节: {sec_count}")

    # 3. 导入编码（批量，每 1000 条提交一次）
    code_count = 0
    batch = []
    for _, row in data.iterrows():
        sec_id = section_map.get(str(row['section_range']))
        diag_code = str(row['diag_code']).strip()
        diag_name = str(row['diag_name']).strip()

        if sec_id and diag_code and diag_code != 'nan':
            batch.append((sec_id, diag_code, diag_name))
            code_count += 1

        if len(batch) >= 1000:
            cursor.executemany(
                "INSERT OR IGNORE INTO icd10_codes (section_id, code, name) VALUES (?,?,?)",
                batch
            )
            conn.commit()
            batch = []

    if batch:
        cursor.executemany(
            "INSERT OR IGNORE INTO icd10_codes (section_id, code, name) VALUES (?,?,?)",
            batch
        )
        conn.commit()

    print(f"编码: {code_count}")

    # 验证
    chk = cursor.execute("SELECT COUNT(*) FROM icd10_codes").fetchone()[0]
    print(f"✓ 数据库实际编码数: {chk}")
    return chk


def import_icd9(conn):
    """导入 ICD-9-CM3 手术操作编码（直接解析 HTML）"""
    import re

    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

    print("\n" + "="*60)
    print("导入 ICD-9-CM3 手术操作编码")
    print("="*60)

    path = os.path.join(DIR, ICD9_FILE)
    if not os.path.exists(path):
        print(f"[ERROR] 文件不存在: {path}")
        return

    # 读取 HTML 并手动解析表格（pd.read_html 对此格式支持不好）
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    print(f"文件大小: {len(html):,} 字符")

    # 提取所有行
    rows_raw = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.I)
    print(f"HTML 行数: {len(rows_raw)}")

    parsed_rows = []
    for row_html in rows_raw:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL | re.I)
        cleaned = []
        for c in cells:
            # 去除所有 HTML 标签
            text = re.sub(r'<[^>]+>', '', c)
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&').strip()
            cleaned.append(text)
        parsed_rows.append(cleaned)

    # 第一行是表头
    if not parsed_rows:
        print("[ERROR] 未解析到数据")
        return

    header = parsed_rows[0]
    print(f"表头: {header}")
    print(f"数据行数: {len(parsed_rows) - 1}")

    # 列: 章, 章名称, 类目代码, 类目名称, 亚目代码, 亚目名称, 细目代码, 细目名称, 手术操作代码, 手术操作名称
    data_rows = []
    for row in parsed_rows[1:]:
        if len(row) >= 10:
            proc_code = row[8].strip()
            proc_name = row[9].strip()
            if proc_code:  # 有编码才算有效行
                data_rows.append({
                    'chapter_no': row[0].strip(),
                    'chapter_name': row[1].strip(),
                    'cat_code': row[2].strip(),
                    'cat_name': row[3].strip(),
                    'sub_code': row[4].strip(),
                    'sub_name': row[5].strip(),
                    'detail_code': row[6].strip(),
                    'detail_name': row[7].strip(),
                    'proc_code': proc_code,
                    'proc_name': proc_name
                })

    print(f"有效数据行: {len(data_rows)}")

    cursor = conn.cursor()

    # 清空旧数据
    cursor.execute("DELETE FROM icd9_codes")
    cursor.execute("DELETE FROM icd9_chapters")

    # 1. 收集章信息
    chapters = {}
    for r in data_rows:
        ch_no = r['chapter_no']
        if ch_no and ch_no not in chapters:
            chapters[ch_no] = r['chapter_name']

    # 推导每章编码范围
    ch_codes = {}
    for r in data_rows:
        ch_no = r['chapter_no']
        if ch_no:
            ch_codes.setdefault(ch_no, []).append(r['proc_code'])

    chapter_9_map = {}
    for ch_no, ch_name in chapters.items():
        try:
            ch_int = int(float(ch_no))
        except (ValueError, TypeError):
            continue

        codes_in_ch = sorted(set(ch_codes.get(ch_no, [])))
        ch_range = f"{codes_in_ch[0]}-{codes_in_ch[-1]}" if codes_in_ch else ""

        safe_name = ch_name.replace('/', '-').replace('\\', '-').replace(':', '：')
        safe_name = safe_name.replace('*', '').replace('?', '').replace('"', '')
        safe_name = safe_name.replace('<', '').replace('>', '').replace('|', '')
        safe_name = safe_name.strip()
        if not safe_name:
            safe_name = f"第{ch_int}章"

        folder = f"{ch_int:02d}-{safe_name}({ch_range})"

        cursor.execute(
            "INSERT INTO icd9_chapters (chapter_no, code_range, name, folder_name) VALUES (?,?,?,?)",
            (ch_int, ch_range, ch_name, folder)
        )
        chapter_9_map[ch_no] = cursor.lastrowid

    print(f"章节: {len(chapter_9_map)}")

    # 2. 批量导入编码
    code_count = 0
    batch = []
    for r in data_rows:
        ch_id = chapter_9_map.get(r['chapter_no'])
        if ch_id:
            batch.append((ch_id, r['proc_code'], r['proc_name']))
            code_count += 1

        if len(batch) >= 2000:
            cursor.executemany(
                "INSERT OR IGNORE INTO icd9_codes (chapter_id, code, name) VALUES (?,?,?)",
                batch
            )
            conn.commit()
            print(f"  已导入 {code_count} 条...")
            batch = []

    if batch:
        cursor.executemany(
            "INSERT OR IGNORE INTO icd9_codes (chapter_id, code, name) VALUES (?,?,?)",
            batch
        )
        conn.commit()

    print(f"编码总数: {code_count}")

    chk = cursor.execute("SELECT COUNT(*) FROM icd9_codes").fetchone()[0]
    print(f"✓ 数据库实际编码数: {chk}")
    return chk


def verify(conn):
    """验证导入结果"""
    cursor = conn.cursor()
    print("\n" + "="*60)
    print("验证导入结果")
    print("="*60)

    ch_count = cursor.execute("SELECT COUNT(*) FROM icd10_chapters").fetchone()[0]
    sec_count = cursor.execute("SELECT COUNT(*) FROM icd10_sections").fetchone()[0]
    code10_count = cursor.execute("SELECT COUNT(*) FROM icd10_codes").fetchone()[0]

    ch9_count = cursor.execute("SELECT COUNT(*) FROM icd9_chapters").fetchone()[0]
    code9_count = cursor.execute("SELECT COUNT(*) FROM icd9_codes").fetchone()[0]

    print(f"ICD-10: {ch_count} 章 · {sec_count} 节 · {code10_count} 条编码")
    print(f"ICD-9:  {ch9_count} 章 · {code9_count} 条编码")

    # 取样
    print("\n--- ICD-10 样本 ---")
    for row in cursor.execute("SELECT code, name FROM icd10_codes LIMIT 10").fetchall():
        print(f"  {row[0]}  {row[1]}")

    print("\n--- ICD-9 样本 ---")
    for row in cursor.execute("SELECT code, name FROM icd9_codes LIMIT 10").fetchall():
        print(f"  {row[0]}  {row[1]}")

    # 各章统计
    print("\n--- ICD-10 各章编码数 ---")
    for row in cursor.execute(
        "SELECT ch.chapter_no, ch.name, COUNT(c.id) "
        "FROM icd10_chapters ch "
        "JOIN icd10_sections s ON s.chapter_id=ch.id "
        "JOIN icd10_codes c ON c.section_id=s.id "
        "GROUP BY ch.id ORDER BY ch.chapter_no"
    ).fetchall():
        print(f"  第{row[0]}章: {row[2]} 条 - {row[1]}")


def main():
    print("ICD 官方数据导入器")
    print(f"数据库: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("[ERROR] 数据库不存在，请先运行 init_db.py")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")

    try:
        n10 = import_icd10(conn)
        n9 = import_icd9(conn)
        verify(conn)

        print("\n" + "="*60)
        print("导入完成！")
        print(f"  ICD-10: {n10} 条编码")
        print(f"  ICD-9:  {n9} 条编码")
        print(f"\n下一步:")
        print(f"  python generate_md.py       → 刷新 Obsidian 笔记")
        print(f"  python generate_web_json.py → 刷新网页数据")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
