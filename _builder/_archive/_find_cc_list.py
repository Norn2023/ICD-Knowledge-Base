import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    # Search for "MCC表" or "CC表" or "严重合并症" patterns
    print("=== Searching for actual MCC/CC code lists in main body ===")

    # Check after the TOC section - the actual definition tables
    for pn in range(40, 100):
        text = pdf.pages[pn].extract_text() or ""
        # Look for patterns like "MCC" or "严重合并症" in table headers
        if any(kw in text[:500] for kw in ['MCC', '严重合并', '并发症与合并']):
            lines = [l.strip() for l in text.split('\n')[:10] if l.strip()]
            print(f"\nPage {pn+1}:")
            for l in lines:
                print(f"  {l[:150]}")

    # Also check the section around page 37-50 more carefully
    print("\n\n=== Pages 37-50 full text ===")
    for pn in range(36, 50):
        text = pdf.pages[pn].extract_text() or ""
        tables = pdf.pages[pn].extract_tables()
        if not tables and len(text) < 200:
            continue
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        has_t = len(tables) > 0
        print(f"\nPage {pn+1} {'[TABLE]' if has_t else ''}:")
        for l in lines[:8]:
            print(f"  {l[:150]}")

    # Check Appendix area for table 6-3-1 (MCC/CC list?)
    print("\n\n=== Checking Appendix table names (pages 1486-1500) ===")
    for pn in range(1485, 1510):
        text = pdf.pages[pn].extract_text() or ""
        tables = pdf.pages[pn].extract_tables()
        first_line = text.split('\n')[0].strip() if text else ""
        if first_line:
            print(f"Page {pn+1}: {first_line[:120]}")
