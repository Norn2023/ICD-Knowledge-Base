import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Exploring DRG PDF - finding key table sections...")
print()

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    total = len(pdf.pages)

    # Sample pages at intervals to find ADRG/DRG tables and MDC main diagnosis tables
    # Based on TOC: BB4 at p94, CD1 at p170, DU1 at p259, FF3 at p357, GB2 at p410,
    #               HS2 at p461, MDCL at p665, NF1 at p728, QJ1 at p822, SV1 at p911,
    #               MDCX at p1033

    key_pages = [94, 170, 259, 357, 410, 461, 665, 728, 822, 911, 1033]

    for page_no in key_pages:
        if page_no <= total:
            p = pdf.pages[page_no - 1]  # 0-indexed
            tables = p.extract_tables()
            text = (p.extract_text() or "")[:200]

            if tables:
                t = tables[0]
                nrows = len(t)
                ncols = len(t[0]) if t else 0
                header = t[0]
                print(f"Page {page_no}: {nrows} rows x {ncols} cols")
                print(f"  Header: {header}")
                # Show first few data rows
                for i in range(1, min(4, nrows)):
                    print(f"  {t[i]}")
                print()

    # Also look at pages around 1486+ for appendix tables
    print("--- Appendix tables ---")
    for page_no in [1486, 1543, 1601, 1660, 1830]:
        if page_no <= total:
            p = pdf.pages[page_no - 1]
            tables = p.extract_tables()
            text = (p.extract_text() or "")[:200]
            if tables:
                t = tables[0]
                print(f"Page {page_no}: {len(t)}r x {len(t[0])}c -> {t[0][:6]}")
                print(f"  Sample: {t[1][:6] if len(t)>1 else 'N/A'}")

    # Find where main diagnosis tables start in section 6
    print("\n--- Searching for MDC diagnosis tables (section 6) ---")
    for page_no in range(660, min(670, total)):
        p = pdf.pages[page_no]
        text = (p.extract_text() or "")[:300]
        if "主诊表" in text or "MDC" in text[:100]:
            tables = p.extract_tables()
            if tables:
                t = tables[0]
                print(f"Page {page_no+1}: {len(t)}r x {len(t[0])}c -> {t[0]}")
