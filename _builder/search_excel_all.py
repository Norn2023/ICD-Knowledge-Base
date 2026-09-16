#!/usr/bin/env python3
"""Search ALL sheets of CHS-DRG Excel for 93.38 procedure codes"""
import pandas as pd
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

EXCEL = 'CHS-DRG2.0完整版.xlsx'

# Get all sheet names
xl = pd.ExcelFile(EXCEL, engine='openpyxl')
print(f"Sheet names ({len(xl.sheet_names)}):")
for i, s in enumerate(xl.sheet_names):
    print(f"  [{i}] {repr(s)}")

# Search each sheet for 93.38
print("\n\n=== Searching ALL sheets for 93.38 ===")
for sname in xl.sheet_names:
    try:
        df = pd.read_excel(EXCEL, sheet_name=sname, engine='openpyxl', dtype=str)
        # Search all cells
        found = False
        for col in df.columns:
            mask = df[col].astype(str).str.contains('93.38', na=False, regex=False)
            if mask.any():
                if not found:
                    print(f"\n--- Sheet: {repr(sname)} ---")
                    found = True
                for idx in df[mask].index:
                    row_vals = [str(df.loc[idx, c])[:60] for c in df.columns]
                    print(f"  Row {idx}: Col '{col}' = {df.loc[idx, col]}")
                    print(f"    Full row: {row_vals}")
    except Exception as e:
        print(f"  Sheet {repr(sname)} error: {e}")

print("\n\n=== Searching for 联合物理 ===")
for sname in xl.sheet_names:
    try:
        df = pd.read_excel(EXCEL, sheet_name=sname, engine='openpyxl', dtype=str)
        found = False
        for col in df.columns:
            mask = df[col].astype(str).str.contains('联合物理', na=False)
            if mask.any():
                if not found:
                    print(f"\n--- Sheet: {repr(sname)} ---")
                    found = True
                for idx in df[mask].index:
                    row_vals = [str(df.loc[idx, c])[:80] for c in df.columns]
                    print(f"  Row {idx}: Col '{col}' = {df.loc[idx, col]}")
                    print(f"    Full row: {row_vals}")
    except Exception as e:
        print(f"  Sheet {repr(sname)} error: {e}")

print("\n\n=== Searching for 物理治疗 (in ALL sheets) ===")
for sname in xl.sheet_names:
    try:
        df = pd.read_excel(EXCEL, sheet_name=sname, engine='openpyxl', dtype=str)
        found = False
        for col in df.columns:
            mask = df[col].astype(str).str.contains('物理治疗', na=False)
            if mask.any():
                if not found:
                    print(f"\n--- Sheet: {repr(sname)} ---")
                    found = True
                for idx in df[mask].index:
                    row_vals = [str(df.loc[idx, c])[:80] for c in df.columns]
                    print(f"  Row {idx}: Col '{col}' = {df.loc[idx, col]}")
                    print(f"    Full row: {row_vals}")
    except Exception as e:
        print(f"  Sheet {repr(sname)} error: {e}")
