"""Extract DIP core disease data from 2.0 PDF into database"""
import sys, re, fitz, sqlite3, os

sys.stdout.reconfigure(encoding='utf-8')
PDF_PATH = os.path.join(os.path.dirname(__file__),
    '按病种分值（DIP）付费病种库（2.0版）202407.pdf')
DB_PATH = os.path.join(os.path.dirname(__file__), 'icd_kb.db')

def extract():
    pdf = fitz.open(PDF_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Recreate DIP table with full schema
    cur.execute("DROP TABLE IF EXISTS dip_groups")
    cur.execute("""CREATE TABLE dip_groups (
        id INTEGER PRIMARY KEY,
        dip_code TEXT,
        dx_code TEXT,
        dx_name TEXT,
        px_code TEXT,
        px_name TEXT,
        rel_px_code TEXT,
        rel_px_name TEXT,
        avg_cost REAL DEFAULT 0,
        weight REAL DEFAULT 0
    )""")

    icd10_pattern = re.compile(r'^[A-Z]\d{2}[\.\s]')
    icd9_pattern = re.compile(r'^\d{2}[\.\s]')

    records = []
    total_lines = 0

    for page_num in range(pdf.page_count):
        text = pdf[page_num].get_text()
        lines = text.strip().split('\n')

        # Skip header line (contains column names)
        i = 0
        # Find first data line (starts with a number)
        while i < len(lines):
            line = lines[i].strip()
            if line.isdigit() and len(line) <= 5:
                break
            i += 1

        # Parse entries
        while i < len(lines):
            line = lines[i].strip()
            if not line.isdigit():
                i += 1
                continue

            dip_num = int(line)
            i += 1

            if i >= len(lines): break

            # Next line should be ICD-10 code
            dx_code = lines[i].strip()
            i += 1

            if i >= len(lines): break

            # Next line should be diagnosis name (or could be ICD-10 if code spans 2 lines)
            next_line = lines[i].strip()
            i += 1

            dx_name = next_line

            # Default values
            px_code = None
            px_name = None
            rel_px_code = None
            rel_px_name = None

            # Check if there's a procedure (next line is ICD-9 code or empty/new entry)
            if i < len(lines):
                peek = lines[i].strip()
                # ICD-9 codes start with 2 digits + dot
                if icd9_pattern.match(peek):
                    px_code = peek
                    i += 1
                    if i < len(lines):
                        px_name = lines[i].strip()
                        i += 1

                    # Check for related procedure
                    if i < len(lines):
                        peek2 = lines[i].strip()
                        if icd9_pattern.match(peek2):
                            rel_px_code = peek2
                            i += 1
                            if i < len(lines):
                                rel_px_name = lines[i].strip()
                                i += 1

            dip_code = f"DIP{dip_num}"
            records.append((dip_code, dx_code, dx_name, px_code, px_name, rel_px_code, rel_px_name))
            total_lines += 1

    # Insert into database
    cur.executemany(
        "INSERT INTO dip_groups (dip_code, dx_code, dx_name, px_code, px_name, rel_px_code, rel_px_name) VALUES (?,?,?,?,?,?,?)",
        records
    )
    conn.commit()

    # Stats
    total = len(records)
    with_px = sum(1 for r in records if r[3])
    with_rel = sum(1 for r in records if r[5])
    unique_dx = len(set(r[1] for r in records))

    print(f"Extracted {total} DIP records from {pdf.page_count} pages")
    print(f"  With procedure: {with_px} ({with_px*100//total}%)")
    print(f"  With related procedure: {with_rel}")
    print(f"  Unique diagnoses: {unique_dx}")

    # Show samples
    print("\nSample records:")
    for r in records[:5]:
        print(f"  {r[0]}: {r[1]} {r[2][:40]} | px={r[3]} {r[4] if r[4] else ''}")

    print("\nRecords with related procedures:")
    for r in records:
        if r[5]:
            print(f"  {r[0]}: {r[1]} | px={r[3]} | rel_px={r[5]} {r[6][:30] if r[6] else ''}")
            if sum(1 for x in records if x[5]) > 5:
                break

    pdf.close()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    extract()
