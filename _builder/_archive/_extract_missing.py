"""Extract missing DRG data: procedure mappings + exclusion lists"""
import pdfplumber
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    total = len(pdf.pages)

    # 1. Check "不作为分组规则" section (TOC says page 14)
    print("=== 1. 不作为分组规则的疾病诊断和手术操作列表 ===")
    for pn in range(13, 25):
        text = pdf.pages[pn].extract_text() or ""
        if '不作为' in text or '不用于分组' in text or '分组规则' in text:
            lines = [l.strip() for l in text.split('\n')[:30] if l.strip()]
            print(f"  Page {pn+1}:")
            for l in lines[:15]:
                print(f"    {l[:150]}")

    # 2. Check surgical ADRG procedure mappings (pages 65+)
    print("\n=== 2. 手术类ADRG 的手术操作映射 ===")
    proc_count = 0
    for pn in range(64, 200):
        text = pdf.pages[pn].extract_text() or ""
        if '包含以下主要手术或操作' in text or '包含以下主要手术' in text:
            proc_count += 1
            if proc_count <= 5:
                snippet = text[:400].replace('\n', ' | ')
                print(f"\n  Page {pn+1}:")
                print(f"    {snippet[:300]}")

    print(f"\n  共找到 {proc_count} 个含手术映射的页面")

    # 3. Sample page 65+ more carefully
    print("\n\n=== 3. 页65-80 详细内容 ===")
    for pn in range(64, 80):
        text = pdf.pages[pn].extract_text() or ""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        has_key = any('包含以下' in l for l in lines)
        if has_key:
            print(f"\n--- Page {pn+1} ---")
            for l in lines[:12]:
                print(f"  {l[:150]}")

    # 4. Check the full ADRG section structure
    print("\n\n=== 4. ADRG 章节内容结构分析 ===")
    section_types = {'仅诊断': 0, '仅手术': 0, '诊断+手术': 0, '其他': 0}
    for pn in range(64, 1033):
        text = pdf.pages[pn].extract_text() or ""
        has_diag = '包含以下主要诊断' in text
        has_proc = '包含以下主要手术' in text or '包含以下主要手术或操作' in text
        if has_diag and not has_proc:
            section_types['仅诊断'] += 1
        elif has_proc and not has_diag:
            section_types['仅手术'] += 1
        elif has_diag and has_proc:
            section_types['诊断+手术'] += 1
        else:
            section_types['其他'] += 1

    print(f"  仅诊断列表: {section_types['仅诊断']} 页")
    print(f"  仅手术列表: {section_types['仅手术']} 页")
    print(f"  诊断+手术:  {section_types['诊断+手术']} 页")
    print(f"  其他:      {section_types['其他']} 页")

    # 5. Check if "不作为分组规则" has actual code lists
    print("\n\n=== 5. \"不作为分组规则\" 详细 ===")
    for pn in range(14, 30):
        text = pdf.pages[pn].extract_text() or ""
        tables = pdf.pages[pn].extract_tables()
        if '不作为' in text[:200] or '分组规则' in text[:200]:
            print(f"\n  Page {pn+1} {'[TABLE]' if tables else ''}:")
            items = [l.strip() for l in text.split('\n')[:30] if l.strip()]
            for l in items:
                if len(l) > 5:
                    print(f"    {l[:150]}")
