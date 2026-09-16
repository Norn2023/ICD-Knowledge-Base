import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')
df = pd.read_excel('手术主导词2025年11月29日修订少量错误.xlsx', engine='openpyxl')
print('Shape:', df.shape)
print('Cols:', list(df.columns))
print()
for i in range(min(15, len(df))):
    print(f'Row {i}:', list(df.iloc[i]))
print(f'\nTotal rows: {len(df)}')
