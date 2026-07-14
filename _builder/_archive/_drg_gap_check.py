"""Checker: what's in the DRG 2.0 PDF that we haven't extracted?"""
import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    # Check TOC for all sections
    print("=== 目录结构 (pages 3-10) ===")
    for pn in range(2, 12):
        text = pdf.pages[pn].extract_text() or ""
        if '目' in text[:50] or '编制说明' in text or '分组方案' in text:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            for l in lines[:40]:
                # Only show section headers and key items
                if any(k in l for k in ['（', '）', '一、', '二、', '三、', '四、', '五、', '六、',
                                          '表', '附录', 'MDC', 'ADRG', 'DRG', '编制', '环境',
                                          'CC', 'MCC', '手术', '操作']):
                    print(f"  {l[:120]}")

    # Check structure of ADRG pages (94-1033)
    # We know each ADRG has: code, name, "包含以下主要诊断", list of codes
    # What about procedures? Let's sample a few surgical ADRGs
    print("\n=== 抽查手术类 ADRG 页面（看是否有手术映射）===")
    surgical_adrgs = {
        'BB4': 94,   # 伴创伤诊断的颅脑手术
        'CD1': 170,  # 眼眶手术
        'GB2': 410,  # 胃十二指肠大手术
        'FK1': 42,   # 心脏循环辅助系统植入 (need to find actual page)
    }
    # Find actual pages for each
    for code in ['BB4', 'CD1', 'CB1', 'GB2', 'GD1', 'FK1', 'FL1', 'FN1', 'GE1', 'GF1']:
        for pn in range(93, 1034):
            text = pdf.pages[pn].extract_text() or ""
            if len(text) > 50 and code in text[:30]:
                # This is the page where this ADRG starts
                full_text = text
                # Also get next page to see full definition
                if pn + 1 < len(pdf.pages):
                    full_text += '\n' + (pdf.pages[pn+1].extract_text() or "")
                # Check for procedure mentions
                has_proc = '手术' in full_text or '操作' in full_text
                has_diag = '诊断' in full_text or '包含以下' in full_text
                # Look for key sections
                sections_found = []
                if '包含以下主要诊断' in full_text:
                    sections_found.append('主要诊断列表')
                if '包含以下主要手术' in full_text:
                    sections_found.append('主要手术列表')
                if '手术操作' in full_text[:500]:
                    sections_found.append('手术操作')

                print(f"\n  ADRG {code} (页码{pn+1}): {' '.join(sections_found) if sections_found else '仅诊断列表'}")
                # Show first 200 chars
                start = full_text.find(code)
                if start >= 0:
                    snippet = full_text[start:start+300].replace('\n', ' | ')
                    print(f"    {snippet[:200]}")
                break

    # Check pages 1033-1485 (MDC主诊表 section)
    print("\n=== MDC主诊表区域 (pages 1033-1485) ===")
    for pn in [1032, 1033, 1034, 1035, 1100, 1200]:
        text = pdf.pages[pn].extract_text() or ""
        first_line = text.split('\n')[0].strip() if text else "(empty)"
        chars = len(text)
        print(f"  Page {pn+1}: {first_line[:100]}... ({chars} chars)")

    # Check for procedure/operation mapping tables
    print("\n=== 搜索：手术操作相关表格 ===")
    for keyword in ['手术操作编码', '手术操作与ADRG', '主要手术', '包含以下主要手术']:
        found = False
        for pn in range(0, min(500, len(pdf.pages))):
            text = pdf.pages[pn].extract_text() or ""
            if keyword in text:
                if not found:
                    print(f"  '{keyword}' 出现在: 页码{pn+1}")
                    found = True
                    # Show context
                    idx = text.find(keyword)
                    print(f"    {text[max(0,idx-30):idx+100].replace(chr(10),' | ')[:150]}")
        if not found:
            print(f"  '{keyword}': 未找到")

    # Check if there are separate CC/MCC lists (not just exclusion tables)
    print("\n=== 搜索：MCC/CC 码表 ===")
    for keyword in ['MCC表', 'CC表', 'MCC列表', 'CC列表', '严重合并症列表']:
        found_pages = []
        for pn in range(0, len(pdf.pages)):
            text = pdf.pages[pn].extract_text() or ""
            if keyword in text:
                found_pages.append(pn+1)
                if len(found_pages) <= 3:
                    print(f"  '{keyword}' 页码{pn+1}")
        if not found_pages:
            print(f"  '{keyword}': 未找到")
