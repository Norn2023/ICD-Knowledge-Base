import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    # Check page 94-98 (BB4 section start)
    for pn in [94, 95, 96, 97, 100, 150, 200, 300, 400, 500, 600, 665, 670, 700, 800, 1000, 1200, 1400]:
        if pn > len(pdf.pages):
            continue
        p = pdf.pages[pn - 1]
        text = (p.extract_text() or "")
        tables = p.extract_tables()

        has_table = len(tables) > 0
        print(f"\n=== Page {pn} === {'[TABLE]' if has_table else '[TEXT]'} {len(text)} chars")

        # Show first 400 chars of text
        lines = text.split('\n')
        for i, line in enumerate(lines[:25]):
            line = line.strip()
            if line:
                print(f"  {line}")

        # If table, show structure
        if has_table:
            t = tables[0]
            print(f"  TABLE: {len(t)} rows x {len(t[0])} cols")
            print(f"  Header: {t[0]}")
            for row in t[1:4]:
                print(f"  Data: {row}")
