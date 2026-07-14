import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    total = len(pdf.pages)

    # Search the full text for CC/MCC references
    print("Searching for CC/MCC keywords...")

    # Check table of contents (pages 4-20)
    for i in range(3, 25):
        text = pdf.pages[i].extract_text() or ""
        if "CC" in text or "MCC" in text or "并发症" in text or "合并症" in text:
            print(f"\nPage {i+1}:")
            for line in text.split('\n')[:30]:
                if "CC" in line or "MCC" in line or "并发症" in line or "合并症" in line:
                    print(f"  {line.strip()[:120]}")

    # Search entire text for "MCC" patterns
    print("\n\nScanning all pages for explicit CC/MCC sections...")
    found_pages = []
    for i in range(total):
        text = pdf.pages[i].extract_text() or ""
        if "严重并发症与合并症" in text or "并发症与合并症" in text or "MCC表" in text or "CC表" in text:
            found_pages.append(i+1)

    print(f"Pages with CC/MCC section headers: {found_pages}")

    # Check appendix area (pages 1486-1834)
    print("\n\nChecking appendix area...")
    for pn in [1485, 1486, 1487, 1488, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1830]:
        if pn <= total:
            text = pdf.pages[pn-1].extract_text() or ""
            tables = pdf.pages[pn-1].extract_tables()
            first_lines = ' | '.join([l.strip() for l in text.split('\n')[:5] if l.strip()])
            has_t = len(tables) > 0
            print(f"  Page {pn}: {'[TABLE]' if has_t else '[TEXT]'} - {first_lines[:150]}...")

    # Also check page ~1033 onwards where the MDC section continues
    print("\n\nChecking after MDC section (pages 1030-1485)...")
    for pn in [1033, 1100, 1200, 1300, 1400, 1480]:
        if pn <= total:
            text = pdf.pages[pn-1].extract_text() or ""
            first_lines = ' | '.join([l.strip() for l in text.split('\n')[:5] if l.strip()])
            print(f"  Page {pn}: {first_lines[:150]}...")
