import pdfplumber
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Only check first 20 pages max
MAX_PAGES = 20

print("=" * 60)
print("DRG PDF - first pages")
print("=" * 60)
with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}")
    for i in range(min(MAX_PAGES, total)):
        p = pdf.pages[i]
        tables = p.extract_tables()
        text = (p.extract_text() or "")[:200]
        if tables:
            t = tables[0]
            print(f"\nPage {i+1}: {len(tables)} tables, {len(t)} rows")
            for j in range(min(6, len(t))):
                print(f"  {t[j][:8] if len(t[j])>8 else t[j]}")
        if text.strip():
            print(f"  text: {text[:150]}...")

print("\n" + "=" * 60)
print("DIP PDF - first pages")
print("=" * 60)
with pdfplumber.open("按病种分值（DIP）付费病种库（2.0版）202407.pdf") as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}")
    for i in range(min(MAX_PAGES, total)):
        p = pdf.pages[i]
        tables = p.extract_tables()
        text = (p.extract_text() or "")[:200]
        if tables:
            t = tables[0]
            print(f"\nPage {i+1}: {len(tables)} tables, {len(t)} rows")
            for j in range(min(6, len(t))):
                row = t[j]
                print(f"  {row[:8] if len(row)>8 else row}")
        if text.strip():
            print(f"  text: {text[:150]}...")
