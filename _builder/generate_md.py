#!/usr/bin/env python3
"""
ICD 编码知识库 · Markdown 生成器
从 SQLite 数据库生成 Obsidian Markdown 笔记
运行：python generate_md.py
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "icd_kb.db")
VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def generate():
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    total_files = 0

    # ── ICD-10 章节索引 ──────────────────────────────────
    cur.execute("SELECT * FROM icd10_chapters ORDER BY chapter_no")
    chapters = cur.fetchall()
    total_files += len(chapters)

    for ch in chapters:
        sections = cur.execute(
            "SELECT * FROM icd10_sections WHERE chapter_id=? ORDER BY code_range",
            (ch["id"],)
        ).fetchall()

        # 统计编码数
        code_count = cur.execute(
            "SELECT COUNT(*) as cnt FROM icd10_codes WHERE section_id IN "
            "(SELECT id FROM icd10_sections WHERE chapter_id=?)",
            (ch["id"],)
        ).fetchone()["cnt"]

        folder = os.path.join(VAULT_ROOT, "ICD10-疾病诊断", ch["folder_name"])
        os.makedirs(folder, exist_ok=True)

        # _index.md 章节索引
        sec_rows = ""
        for s in sections:
            file_name = f"{s['code_range']}-{s['name'].replace('/','-')}.md"
            sec_rows += f"| {s['code_range']} | {s['name']} | "
            sec_rows += f"[[ICD10-疾病诊断/{ch['folder_name']}/{file_name}|→]] |\n"

        index_md = f"""---
tags:
  - icd10
  - chapter
  - chapter-{ch['chapter_no']:02d}
status: auto-generated
created: 2026-06-18
---

# 第{ch['chapter_no']}章 {ch['name']}

- **编码范围**：{ch['code_range']}
- **章编号**：第 {ch['chapter_no']} 章
- **编码数量**：{code_count} 条

## 概述

<!-- 本章涵盖的疾病类别 -->

## 类目/节列表

| 编码范围 | 名称 | 文件 |
|---------|------|------|
{sec_rows}

## 相关章节

- [[ICD10-疾病诊断/_index|ICD-10 总索引]]

## 参考资料

- ICD-10 官方卷 1 第{ch['chapter_no']}章
"""
        with open(os.path.join(folder, "_index.md"), "w", encoding="utf-8") as f:
            f.write(index_md)

        # 每个节一个文件
        for s in sections:
            codes = cur.execute(
                "SELECT * FROM icd10_codes WHERE section_id=? ORDER BY code",
                (s["id"],)
            ).fetchall()

            code_rows = ""
            for c in codes:
                notes = c["notes"] or ""
                code_rows += f"| {c['code']} | {c['name']} | {notes} |\n"

            includes = s["includes"] or "—"
            excludes = s["excludes"] or "—"
            rules = s["rules"] or "—"

            file_name = f"{s['code_range']}-{s['name'].replace('/','-')}.md"
            section_md = f"""---
tags:
  - icd10
  - section
  - chapter-{ch['chapter_no']:02d}
status: auto-generated
created: 2026-06-18
---

# {s['code_range']} {s['name']}

- **编码范围**：{s['code_range']}
- **所属章节**：[[ICD10-疾病诊断/{ch['folder_name']}/_index|第{ch['chapter_no']}章 {ch['name']}]]

## 编码列表

| 编码 | 名称 | 备注 |
|-----|------|------|
{code_rows}

## 包括/不包括

- **包括**：{includes}
- **不包括**：{excludes}

## 编码规则

{rules}

## 常见错误

<!-- 容易混淆的编码 -->

## 相关链接

- [[ICD10-疾病诊断/{ch['folder_name']}/_index|返回第{ch['chapter_no']}章索引]]
"""
            with open(os.path.join(folder, file_name), "w", encoding="utf-8") as f:
                f.write(section_md)
            total_files += 1

    # ── ICD-9 章节索引 ──────────────────────────────────
    cur.execute("SELECT * FROM icd9_chapters ORDER BY chapter_no")
    ch9s = cur.fetchall()

    for ch9 in ch9s:
        codes = cur.execute(
            "SELECT * FROM icd9_codes WHERE chapter_id=? ORDER BY code",
            (ch9["id"],)
        ).fetchall()

        folder = os.path.join(VAULT_ROOT, "ICD9-手术操作", ch9["folder_name"])
        os.makedirs(folder, exist_ok=True)

        code_rows = ""
        for c in codes:
            code_rows += f"| {c['code']} | {c['name']} | {c['notes'] or ''} |\n"

        index_md = f"""---
tags:
  - icd9
  - chapter
  - chapter-{ch9['chapter_no']:02d}
status: auto-generated
created: 2026-06-18
---

# 第{ch9['chapter_no']}章 {ch9['name']}

- **编码范围**：{ch9['code_range']}
- **编码数量**：{len(codes)} 条

## 编码列表

| 编码 | 名称 | 备注 |
|-----|------|------|
{code_rows}

## 编码要点

{ch9['notes'] or '—'}

## 相关链接

- [[ICD9-手术操作/_index|ICD-9 总索引]]
"""
        with open(os.path.join(folder, "_index.md"), "w", encoding="utf-8") as f:
            f.write(index_md)
        total_files += 1

    # ── 案例笔记 ────────────────────────────────────────
    cases_folder = os.path.join(VAULT_ROOT, "ICD10-疾病诊断", "_案例库")
    os.makedirs(cases_folder, exist_ok=True)

    cur.execute("SELECT * FROM cases ORDER BY case_no")
    cases = cur.fetchall()

    for case in cases:
        diags = cur.execute(
            "SELECT cd.rank, ic.code, ic.name FROM case_diagnoses cd "
            "JOIN icd10_codes ic ON cd.icd10_id=ic.id WHERE cd.case_id=? ORDER BY cd.rank",
            (case["id"],)
        ).fetchall()

        procs = cur.execute(
            "SELECT cp.rank, ic9.code, ic9.name FROM case_procedures cp "
            "JOIN icd9_codes ic9 ON cp.icd9_id=ic9.id WHERE cp.case_id=? ORDER BY cp.rank",
            (case["id"],)
        ).fetchall()

        diag_rows = ""
        for d in diags:
            label = "★ 主要诊断" if d["rank"] == 1 else f"其他诊断 {d['rank']-1}"
            diag_rows += f"| {label} | {d['code']} | {d['name']} |\n"

        proc_rows = ""
        for p in procs:
            label = "★ 主要手术" if p["rank"] == 1 else f"其他手术 {p['rank']-1}"
            proc_rows += f"| {label} | {p['code']} | {p['name']} |\n"

        if not proc_rows:
            proc_rows = "| — | — | 无手术操作 |\n"

        case_md = f"""---
tags:
  - case
  - icd10
  - icd9
  - drg
status: auto-generated
created: 2026-06-18
---

# {case['case_no']}

| 项目 | 值 |
|------|-----|
| **性别** | {'男' if case['gender']=='M' else '女' if case['gender']=='F' else '—'} |
| **年龄** | {case['age']} 岁 |
| **入院** | {case['admission']} |
| **出院** | {case['discharge']} |
| **科室** | {case['dept']} |
| **费用** | ¥{case['total_cost']:,.2f} |
| **DRG 入组** | [[DRG-分组/{case['drg_result']}\\|{case['drg_result']}]] |
| **DIP 入组** | {case['dip_result'] or '—'} |

## 诊断

{diag_rows}

## 手术/操作

{proc_rows}

## 病史摘要

{case['notes']}

## 相关病例

<!-- 添加相似病例的 [[链接]] -->

---
"""
        with open(os.path.join(cases_folder, f"{case['case_no']}.md"), "w", encoding="utf-8") as f:
            f.write(case_md)
        total_files += 1

    # ── DRG 分组索引 ────────────────────────────────────
    drg_folder = os.path.join(VAULT_ROOT, "DRG-分组")
    os.makedirs(drg_folder, exist_ok=True)

    cur.execute("SELECT * FROM drg_mdc ORDER BY mdc_code")
    mdcs = cur.fetchall()

    mdc_rows = ""
    for m in mdcs:
        adrg_count = cur.execute(
            "SELECT COUNT(*) FROM drg_adrg WHERE mdc_id=?", (m["id"],)
        ).fetchone()[0]
        mdc_rows += f"| {m['mdc_code']} | {m['name']} | {adrg_count} |\n"

    # ADRG 列表
    cur.execute("""
        SELECT a.adrg_code, a.name, a.category, m.mdc_code, m.name as mdc_name,
               (SELECT COUNT(*) FROM adrg_diagnosis_map adm WHERE adm.adrg_id=a.id) as dx_count,
               (SELECT COUNT(*) FROM adrg_procedure_map apm WHERE apm.adrg_id=a.id) as px_count
        FROM drg_adrg a
        LEFT JOIN drg_mdc m ON a.mdc_id=m.id
        ORDER BY a.adrg_code
    """)
    adrgs = cur.fetchall()

    # ADRG summary table: show first 50, rest collapsed
    adrg_rows = ""
    for a in adrgs[:50]:
        adrg_rows += f"| {a['adrg_code']} | {a['name']} | {a['category'] or '—'} | {a['mdc_code'] or '—'} | {a['dx_count'] or 0} | {a['px_count'] or 0} |\n"

    if len(adrgs) > 50:
        adrg_rows += f"| ... | +{len(adrgs)-50} 个更多分组，见 Web 应用 | ... | ... | ... | ... |\n"

    # DRG severity counts
    drg_count = cur.execute("SELECT COUNT(*) FROM drg_groups").fetchone()[0]
    mcc_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='MCC'").fetchone()[0]
    cc_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='CC'").fetchone()[0]
    nocc_count = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='noCC'").fetchone()[0]
    stat_dxmap = cur.execute("SELECT COUNT(*) FROM adrg_diagnosis_map").fetchone()[0]
    stat_procmap = cur.execute("SELECT COUNT(*) FROM adrg_procedure_map").fetchone()[0]

    drg_index = f"""---
tags:
  - drg
  - index
status: auto-generated
created: 2026-06-18
---

# CHS-DRG 2.0 分组索引

## 数据统计

- MDC: {len(mdcs)} 个
- ADRG: {len(adrgs)} 个
- DRG: {drg_count} 个
  - MCC: {mcc_count} | CC: {cc_count} | noCC: {nocc_count}
- 诊断映射: {stat_dxmap} 条
- 手术映射: {stat_procmap} 条

## MDC 总览

| MDC | 名称 | ADRG 数量 |
|-----|------|----------|
{mdc_rows}

## ADRG 分组（前50条）

| 编码 | 名称 | 类别 | MDC | 诊断映射 | 手术映射 |
|------|------|------|-----|---------|---------|
{adrg_rows}

## 相关链接

- [[ICD10-疾病诊断/_index|ICD-10 诊断编码]]
- [[ICD9-手术操作/_index|ICD-9 手术编码]]
- [[DIP-病种/_index|DIP 2.0 病种]]
"""
    with open(os.path.join(drg_folder, "_index.md"), "w", encoding="utf-8") as f:
        f.write(drg_index)
    total_files += 1

    # ── DIP 分组索引（按 ICD-10 章拆分）─────────────────
    dip_folder = os.path.join(VAULT_ROOT, "DIP-病种")
    os.makedirs(dip_folder, exist_ok=True)

    cur.execute("SELECT * FROM dip_groups ORDER BY dip_code")
    dips = cur.fetchall()

    # ICD-10 chapter mapping from dx_code prefix
    def dip_chapter(dx_code):
        if not dx_code:
            return 0
        letter = dx_code[0]
        try:
            num = int(dx_code[1:3]) if len(dx_code) >= 3 else 0
        except ValueError:
            num = 0
        if letter in ('A', 'B'):
            return 1
        if letter == 'C' or (letter == 'D' and num < 50):
            return 2
        if letter == 'D' and num >= 50:
            return 3
        if letter == 'E':
            return 4
        if letter == 'F':
            return 5
        if letter == 'G':
            return 6
        if letter == 'H' and num < 60:
            return 7
        if letter == 'H' and num >= 60:
            return 8
        if letter == 'I':
            return 9
        if letter == 'J':
            return 10
        if letter == 'K':
            return 11
        if letter == 'L':
            return 12
        if letter == 'M':
            return 13
        if letter == 'N':
            return 14
        if letter == 'O':
            return 15
        if letter == 'P':
            return 16
        if letter == 'Q':
            return 17
        if letter == 'R':
            return 18
        if letter in ('S', 'T'):
            return 19
        if letter in ('V', 'W', 'X', 'Y'):
            return 20
        if letter == 'Z':
            return 21
        if letter == 'U':
            return 22
        return 0

    # Chapter names matching ICD-10
    ch_names = {
        0: "未分类", 1: "某些传染病和寄生虫病(A00-B99)",
        2: "肿瘤(C00-D48)", 3: "血液及造血器官疾病和涉及免疫机制的某些疾患(D50-D89)",
        4: "内分泌、营养和代谢疾病(E00-E90)", 5: "精神和行为障碍(F00-F99)",
        6: "神经系统疾病(G00-G99)", 7: "眼和附器疾病(H00-H59)",
        8: "耳和乳突疾病(H60-H95)", 9: "循环系统疾病(I00-I99)",
        10: "呼吸系统疾病(J00-J99)", 11: "消化系统疾病(K00-K93)",
        12: "皮肤和皮下组织疾病(L00-L99)", 13: "肌肉骨骼系统和结缔组织疾病(M00-M99)",
        14: "泌尿生殖系统疾病(N00-N99)", 15: "妊娠、分娩和产褥期(O00-O99)",
        16: "起源于围生期的某些情况(P00-P96)", 17: "先天性畸形、变形和染色体异常(Q00-Q99)",
        18: "症状、体征和临床与实验室异常所见，不可归类在他处者(R00-R99)",
        19: "损伤、中毒和外因的某些其他后果(S00-T98)",
        20: "疾病和死亡的外因(V01-Y98)", 21: "影响健康状态和与保健机构接触的因素(Z00-Z99)",
        22: "用于特殊目的的编码(U00-U85)",
    }

    # Group DIP entries by chapter
    dip_by_ch = {}
    for d in dips:
        ch = dip_chapter(d['dx_code'])
        dip_by_ch.setdefault(ch, []).append(d)

    # Generate per-chapter files
    ch_index_links = ""
    for ch in sorted(dip_by_ch.keys()):
        entries = dip_by_ch[ch]
        ch_name = ch_names.get(ch, f"第{ch}章")
        file_name = f"{ch:02d}-{ch_name}.md"
        folder_path = os.path.join(dip_folder, f"ch{ch:02d}")
        os.makedirs(folder_path, exist_ok=True)

        rows = ""
        for d in entries:
            dx = f"{d['dx_code'] or ''} {d['dx_name'] or ''}".strip() or "—"
            px = f"{d['px_code'] or ''} {d['px_name'] or ''}".strip() or "—"
            rows += f"| {d['dip_code']} | {d['dx_name'] or '—'} | {dx} | {px} | ¥{d['avg_cost'] or 0:,.0f} | {d['weight'] or 0} |\n"

        ch_md = f"""---
tags:
  - dip
  - chapter-{ch:02d}
status: auto-generated
created: 2026-06-18
---

# 第{ch}章 {ch_name}

> DIP 2.0 病种 · 共 {len(entries)} 条

| 编码 | 名称 | 主要诊断 | 主要手术 | 均费 | 权重 |
|------|------|---------|---------|------|------|
{rows}

## 相关链接

- [[DIP-病种/_index|DIP 2.0 总索引]]
"""
        with open(os.path.join(folder_path, "_index.md"), "w", encoding="utf-8") as f:
            f.write(ch_md)

        ch_short = ch_name.split('(')[0].strip()
        ch_index_links += f"| {ch} | {ch_short} | {len(entries)} | [[DIP-病种/ch{ch:02d}/_index|→]] |\n"
        total_files += 1

    # Root index
    dip_index_md = f"""---
tags:
  - dip
  - index
status: auto-generated
created: 2026-06-18
---

# DIP 2.0 病种分组索引

> 按 ICD-10 诊断大类分章，共 {len(dips)} 条病种。

## 章总览

| 章 | 诊断大类 | DIP 数量 | 文件 |
|---|---------|---------|------|
{ch_index_links}

## 相关链接

- [[DRG-分组/_index|DRG 2.0 分组]]
- [[ICD10-疾病诊断/_index|ICD-10 编码]]
"""
    with open(os.path.join(dip_folder, "_index.md"), "w", encoding="utf-8") as f:
        f.write(dip_index_md)
    total_files += 1

    # ── 更新欢迎页统计 ──────────────────────────────────
    stat_icd10 = cur.execute("SELECT COUNT(*) FROM icd10_codes").fetchone()[0]
    stat_icd9 = cur.execute("SELECT COUNT(*) FROM icd9_codes").fetchone()[0]
    stat_drg = cur.execute("SELECT COUNT(*) FROM drg_adrg").fetchone()[0]
    stat_drg_groups = cur.execute("SELECT COUNT(*) FROM drg_groups").fetchone()[0]
    stat_mcc = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='MCC'").fetchone()[0]
    stat_cc = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='CC'").fetchone()[0]
    stat_nocc = cur.execute("SELECT COUNT(*) FROM drg_groups WHERE severity='noCC'").fetchone()[0]
    stat_excl = cur.execute("SELECT COUNT(*) FROM cc_exclusions").fetchone()[0]
    stat_dxmap = cur.execute("SELECT COUNT(*) FROM adrg_diagnosis_map").fetchone()[0]
    stat_procmap = cur.execute("SELECT COUNT(*) FROM adrg_procedure_map").fetchone()[0]
    stat_dip = cur.execute("SELECT COUNT(*) FROM dip_groups").fetchone()[0]
    stat_cases = cur.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    stat_mdc = cur.execute("SELECT COUNT(*) FROM drg_mdc").fetchone()[0]

    # Update welcome page stats
    welcome_path = os.path.join(VAULT_ROOT, "欢迎.md")
    welcome_new = f"""---
tags:
  - index
  - home
created: 2026-06-18
---

# ICD 编码知识库

> 基于 Karpathy LLM Wiki + SQLite 数据驱动架构。
> Markdown 即源码，AI 即查询引擎，改数据自动刷新笔记。

---

## 数据统计

- ICD-10 疾病诊断：{stat_icd10} 条编码（22 章）
- ICD-9 手术操作：{stat_icd9} 条编码（18 章）
- DRG 2.0 分组：{stat_mdc} MDC · {stat_drg} ADRG · {stat_drg_groups} DRG
  - 严重合并症/并发症（MCC）：{stat_mcc} 组
  - 一般合并症/并发症（CC）：{stat_cc} 组
  - 不伴合并症/并发症：{stat_nocc} 组
  - CC/MCC 排除记录：{stat_excl} 条
  - 诊断→ADRG 映射：{stat_dxmap} 条
  - 手术→ADRG 映射：{stat_procmap} 条
- DIP 2.0 病种：{stat_dip} 种
- 案例库：{stat_cases} 份

---

## 快速导航

| 区域 | 说明 |
|------|------|
| [[ICD10-疾病诊断/_index\\|ICD-10 诊断]] | 22章 · {stat_icd10} 条编码 |
| [[ICD9-手术操作/_index\\|ICD-9 手术]] | 18章 · {stat_icd9} 条编码 |
| [[DRG-分组/_index\\|DRG 2.0 分组]] | {stat_drg} 个 DRG 组 |
| [[DIP-病种/_index\\|DIP 2.0 病种]] | {stat_dip} 个病种 |
| [[速查手册/常见诊断编码速查\\|常见诊断速查]] | 高频诊断编码 |
| [[速查手册/常见手术编码速查\\|常见手术速查]] | 高频手术编码 |
| [[速查手册/编码规则要点\\|编码规则要点]] | 核心编码规则 |

## 怎么用这个知识库

### 我是 AI，你直接问我就行：

> 查编码 / 查规则 / 对比 / 查案例 / 分析分组

### 你往里面加内容：

- 用 `_模板/` 里的模板填空
- 用 `[[编码名称]]` 链接相关知识
- 用 `#icd10`、`#icd9`、`#drg` 打标签

### 数据驱动更新：

```bash
cd _builder
python init_db.py      # 初始化/更新数据库
python generate_md.py  # 自动生成 Obsidian 笔记
python generate_web.py # 导出网页数据
```

---

## 最近更新

- 2026-06-18：数据库骨架搭建完成，{stat_icd10} 条 ICD-10 + {stat_icd9} 条 ICD-9 编码入库
"""
    with open(welcome_path, "w", encoding="utf-8") as f:
        f.write(welcome_new)

    conn.close()

    print(f"[OK] Generated {total_files} markdown files")
    print(f"     ICD-10: {len(chapters)} chapters with sections")
    print(f"     ICD-9:  {len(ch9s)} chapters with codes")
    print(f"     DRG:   1 index + {stat_drg} groups")
    print(f"     DIP:   1 index with {stat_dip} groups")
    print(f"     Cases: {stat_cases} case notes")
    print(f"     Homepage updated with stats")


if __name__ == "__main__":
    generate()
