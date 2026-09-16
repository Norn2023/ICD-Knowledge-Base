"""Fix MDC-ADRG mapping by parsing PDF section structure"""
import pdfplumber, sqlite3, re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'icd_kb.db')

# Parse MDC section pages (38-1047) to find MDC->ADRG mapping
with pdfplumber.open("按病组（DRG）付费分组方案（2.0版）.pdf") as pdf:
    current_mdc = None
    mdc_adrg = {}  # mdc_code -> [adrg_code, ...]

    for pn in range(37, min(1048, len(pdf.pages))):
        text = pdf.pages[pn].extract_text() or ""
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Find MDC headers: "MDCB 神经系统疾病及功能障碍"
            m = re.match(r'^(MDC[A-Z])\s+(.+)', line)
            if m and len(m.group(2)) > 2:
                current_mdc = m.group(1)
                mdc_name = m.group(2).strip()
                if current_mdc not in mdc_adrg:
                    mdc_adrg[current_mdc] = []
                continue

            # Find ADRG codes under current MDC
            if current_mdc:
                m2 = re.match(r'^([A-Z]{1,2}\d{1,2})\s+(.+)', line)
                if m2:
                    code = m2.group(1)
                    name = m2.group(2).strip()
                    # Skip non-ADRG (headers, page numbers, etc)
                    if '包含以下' in name or '主要' in name or '诊断' in name or '手术' in name:
                        continue
                    if len(code) >= 2 and len(code) <= 4 and len(name) > 1:
                        if code not in mdc_adrg[current_mdc]:
                            mdc_adrg[current_mdc].append(code)

        if (pn+1) % 200 == 0:
            print(f"  进度: {pn+1}")

    # Stats
    total_adrgs = sum(len(v) for v in mdc_adrg.values())
    print(f"\n找到 {len(mdc_adrg)} MDC, {total_adrgs} ADRG 映射")
    for mdc in sorted(mdc_adrg.keys()):
        print(f"  {mdc}: {len(mdc_adrg[mdc])} ADRGs")

    # Update database
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Get MDC IDs
    mdc_ids = {}
    for row in cur.execute("SELECT id, mdc_code FROM drg_mdc").fetchall():
        mdc_ids[row[1]] = row[0]

    # Get ADRG IDs
    adrg_ids = {}
    for row in cur.execute("SELECT id, adrg_code FROM drg_adrg").fetchall():
        adrg_ids[row[1]] = row[0]

    # Update
    updated = 0
    for mdc_code, adrg_codes in mdc_adrg.items():
        mdc_id = mdc_ids.get(mdc_code)
        if not mdc_id:
            print(f"  SKIP {mdc_code}: not in DB")
            continue
        for adrg_code in adrg_codes:
            adrg_id = adrg_ids.get(adrg_code)
            if adrg_id:
                cur.execute("UPDATE drg_adrg SET mdc_id=? WHERE id=?", (mdc_id, adrg_id))
                updated += 1

    conn.commit()
    print(f"\nPDF提取更新了 {updated} 个 ADRG 的 MDC 关联")

    # ── Fallback: prefix-based mapping for remaining ──
    # Standard DRG 2.0: ADRG first letter → MDC
    letter_mdc = {
        'A':'MDCA','B':'MDCB','C':'MDCC','D':'MDCD','E':'MDCE',
        'F':'MDCF','G':'MDCG','H':'MDCH','I':'MDCI','J':'MDCJ',
        'K':'MDCK','L':'MDCL','M':'MDCM','N':'MDCN','O':'MDCO',
        'P':'MDCP','Q':'MDCQ','R':'MDCR','S':'MDCS','T':'MDCT',
        'U':'MDCU','V':'MDCV','W':'MDCW','X':'MDCX','Y':'MDCY','Z':'MDCZ'
    }
    # Special cases for MDCA 先期分组
    prefix_mdca = ['AA','AB','AC','AD','AE','AF','AG','AH','AJ','AK']
    fallback_count = 0
    unmapped = cur.execute("SELECT id, adrg_code FROM drg_adrg WHERE mdc_id IS NULL").fetchall()
    for adrg_id, code in unmapped:
        mdc = None
        # Check prefix-based special cases
        for p in prefix_mdca:
            if code.startswith(p):
                mdc = 'MDCA'
                break
        if not mdc:
            mdc = letter_mdc.get(code[0])
        if mdc and mdc in mdc_ids:
            cur.execute("UPDATE drg_adrg SET mdc_id=? WHERE id=?", (mdc_ids[mdc], adrg_id))
            fallback_count += 1

    conn.commit()
    print(f"前缀补全: {fallback_count} 个")

    # Final verify
    null_count = cur.execute("SELECT COUNT(*) FROM drg_adrg WHERE mdc_id IS NULL").fetchone()[0]
    total = cur.execute("SELECT COUNT(*) FROM drg_adrg").fetchone()[0]
    print(f"剩余未关联: {null_count}/{total}")

    conn.close()
    print("\nDone! python generate_web_json.py 刷新网页")
