import pdfplumber

# ── DRG ──
print("=" * 60)
print("DRG 分组方案 (2.0版)")
print("=" * 60)

with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    print(f"总页数: {len(pdf.pages)}")

    # 看前几页有什么
    for i in range(min(5, len(pdf.pages))):
        page = pdf.pages[i]
        tables = page.extract_tables()
        text = page.extract_text()
        if text:
            # 只显示前 300 字符
            clean = text.replace('\n', ' | ')[:300]
        else:
            clean = "(no text)"
        print(f"\n  Page {i+1}: {len(tables)} table(s) | text: {clean}...")

    # 找第一个有表格的页
    print("\n--- 找第一个有表格的页面 ---")
    for i in range(len(pdf.pages)):
        tables = pdf.pages[i].extract_tables()
        if tables:
            print(f"\nPage {i+1} 有 {len(tables)} 个表格:")
            for j, t in enumerate(tables):
                print(f"  Table {j}: {len(t)} rows x {len(t[0]) if t else 0} cols")
                for k in range(min(5, len(t))):
                    print(f"    Row {k}: {t[k]}")
            break

# ── DIP ──
print("\n" + "=" * 60)
print("DIP 病种库 (2.0版)")
print("=" * 60)

with pdfplumber.open("按病种分值（DIP）付费病种库（2.0版）202407.pdf") as pdf:
    print(f"总页数: {len(pdf.pages)}")

    for i in range(min(3, len(pdf.pages))):
        page = pdf.pages[i]
        tables = page.extract_tables()
        text = page.extract_text()
        if text:
            clean = text.replace('\n', ' | ')[:300]
        else:
            clean = "(no text)"
        print(f"\n  Page {i+1}: {len(tables)} table(s) | text: {clean}...")

    # 找第一个有表格的页
    print("\n--- 找第一个有表格的页面 ---")
    for i in range(len(pdf.pages)):
        tables = pdf.pages[i].extract_tables()
        if tables:
            print(f"\nPage {i+1} 有 {len(tables)} 个表格:")
            for j, t in enumerate(tables):
                print(f"  Table {j}: {len(t)} rows x {len(t[0]) if t else 0} cols")
                for k in range(min(8, len(t))):
                    print(f"    Row {k}: {t[k]}")
            break
