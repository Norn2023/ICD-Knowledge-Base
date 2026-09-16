#!/usr/bin/env python3
"""Examine the CHS-DRG editable Excel and find surgery ADRG tables"""
import openpyxl, sys, os

sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

wb = openpyxl.load_workbook('0. CHS-DRG 2.0 表格可编辑版.xlsx', data_only=True, read_only=True)

# Try to decode sheet names
print("=== Sheet Names ===")
for i, s in enumerate(wb.sheetnames):
    raw_bytes = s.encode('utf-8')
    print(f"  [{i}] {s!r} -> bytes: {raw_bytes}")
    # Try common Chinese encodings
    for enc in ['gbk', 'gb2312', 'cp936', 'big5', 'shift_jis', 'utf-8']:
        try:
            decoded = s.encode('latin-1').decode(enc)
            if decoded != s and any(ord(c) > 127 for c in decoded):
                print(f"      latin1->{enc}: {decoded}")
        except:
            pass

# Now examine each sheet - print first few rows
for si, sname in enumerate(wb.sheetnames):
    ws = wb[sname]
    print(f"\n{'='*60}")
    print(f"Sheet [{si}]: {sname!r}")
    print(f"  Max row: {ws.max_row}, Max col: {ws.max_column}")
    
    # Print first 10 rows
    for ri, row in enumerate(ws.iter_rows(values_only=True)):
        # Convert to string, handle None
        vals = []
        for c in row:
            if c is None:
                vals.append('')
            elif isinstance(c, str):
                # Try to fix encoding
                try:
                    c_fixed = c.encode('latin-1').decode('gbk')
                    vals.append(c_fixed[:80])
                except:
                    vals.append(c[:80])
            else:
                vals.append(str(c)[:80])
        print(f"  Row {ri}: {vals}")
        if ri >= 20:
            print(f"  ... (total {ws.max_row} rows)")
            break
