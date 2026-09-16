import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check sheets first
xl = pd.ExcelFile('CHS-DRG2.0完整版.xlsx', engine='openpyxl')
print('Sheets:', xl.sheet_names)
for sheet in xl.sheet_names:
    df = pd.read_excel('CHS-DRG2.0完整版.xlsx', sheet_name=sheet, engine='openpyxl')
    print(f'\n=== {sheet} ===')
    print(f'Shape: {df.shape}')
    if df.shape[1] > 0:
        print(f'Cols: {list(df.columns)[:10]}')
    for i in range(min(5, len(df))):
        vals = list(df.iloc[i])
        print(f'  Row {i}: {vals[:8]}')
