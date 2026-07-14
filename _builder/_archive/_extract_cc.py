import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    # TOC says CC/MCC on page 14
    # Check pages around 14-30
    print("=== Pages around CC/MCC section (TOC ref page 14) ===")
    for pn in range(13, 35):
        text = pdf.pages[pn].extract_text() or ""
        tables = pdf.pages[pn].extract_tables()
        first_lines = [l.strip() for l in text.split('\n')[:8] if l.strip()]

        has_keyword = any('合并症' in l or '并发症' in l or 'MCC' in l or 'CC' in l for l in first_lines)
        if has_keyword or tables:
            print(f"\n--- Page {pn+1} --- {'[TABLE]' if tables else ''}")
            for l in first_lines:
                print(f"  {l[:150]}")

    # Check the actual CC/MCC list section
    print("\n\n=== Detailed look at pages 14-20 ===")
    for pn in [14, 15, 16, 17, 18, 19, 20]:
        text = pdf.pages[pn-1].extract_text() or ""
        print(f"\n--- Page {pn} --- ({len(text)} chars)")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for l in lines[:20]:
            print(f"  {l[:150]}")

    # Check appendix tables around page 25 which might be the actual CC/MCC list
    print("\n\n=== Looking for actual CC/MCC code lists ===")
    for pn in range(24, 40):
        text = pdf.pages[pn].extract_text() or ""
        tables = pdf.pages[pn].extract_tables()
        if tables or len(text) > 100:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            sample = ' | '.join(lines[:3])
            if any(kw in text for kw in ['MCC', 'CC', '并发症', '合并症', '严重']):
                print(f"\nPage {pn+1}: {'[TABLE]' if tables else '[TEXT]'}")
                print(f"  {sample[:200]}")
